"""
Modbus TCP Server Implementation for TwinGuard-OT.
Hosts industrial registers and exposes them over local Modbus TCP.
Includes event tracing for network anomaly detection.
"""

import asyncio
import threading
import time
from typing import Dict, Any, List, Optional

from pymodbus.simulator import SimData, SimDevice, DataType
from pymodbus.server.server import ModbusTcpServer

from .registers import (
    RegisterMap,
    REG_TANK_LEVEL_SENSOR,
    REG_SETPOINT_LEVEL,
    REG_PUMP_COMMAND,
    REG_VALVE_COMMAND,
    REG_INFLOW_RATE,
    REG_OUTFLOW_RATE,
    REG_ALARM_STATE,
    REG_LOW_THRESHOLD,
    REG_HIGH_THRESHOLD,
    REG_CONTROL_MODE,
    REG_TRUE_TANK_LEVEL,
    REG_PHYSICAL_RESIDUAL,
    TOTAL_REGISTERS,
)


class ModbusTransactionEvent:
    """Represents a recorded Modbus network event."""
    def __init__(
        self,
        timestamp: float,
        client_ip: str,
        function_code: int,
        function_name: str,
        register_address: int,
        register_name: str,
        value: int,
        is_write: bool,
    ) -> None:
        self.timestamp = timestamp
        self.client_ip = client_ip
        self.function_code = function_code
        self.function_name = function_name
        self.register_address = register_address
        self.register_name = register_name
        self.value = value
        self.is_write = is_write

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "client_ip": self.client_ip,
            "function_code": self.function_code,
            "function_name": self.function_name,
            "register_address": self.register_address,
            "register_name": self.register_name,
            "value": self.value,
            "is_write": self.is_write,
        }


class TwinGuardModbusServer:
    """
    Dedicated local Modbus TCP server for the Virtual PLC and Digital Twin.
    Runs asynchronously on an internal thread using the modern PyModbus simulator datastore.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5020, unit_id: int = 1) -> None:
        self.host = host
        self.port = port
        self.unit_id = unit_id

        # Modern SimData/SimDevice datastore (address 0-indexed for 32 registers)
        self._simdata = SimData(address=0, values=[0] * TOTAL_REGISTERS, datatype=DataType.REGISTERS)
        self._simdevice = SimDevice(id=self.unit_id, simdata=self._simdata)

        self._server: Optional[ModbusTcpServer] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running: bool = False
        self._ready_event = threading.Event()
        self._lock = threading.Lock()

        # Audit and event log
        self.event_buffer: List[ModbusTransactionEvent] = []
        self._max_buffer_size: int = 2000
        self.transaction_count: int = 0
        self._last_rate_calc_time: float = time.time()
        self._window_trans_count: int = 0
        self.current_request_rate: float = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_register(self, offset: int) -> int:
        """Reads raw 16-bit register value from datastore (0-based offset)."""
        if not self._server or not self._loop or not self._is_running:
            return self._simdata.values[offset] if 0 <= offset < len(self._simdata.values) else 0
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._server.async_getValues(self.unit_id, 3, offset, 1),
                self._loop
            )
            vals = future.result(timeout=1.0)
            return vals[0] if vals else 0
        except Exception:
            return self._simdata.values[offset] if 0 <= offset < len(self._simdata.values) else 0

    def get_registers(self, start_offset: int, count: int) -> List[int]:
        """Reads multiple raw registers from datastore."""
        if not self._server or not self._loop or not self._is_running:
            return self._simdata.values[start_offset:start_offset + count]
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._server.async_getValues(self.unit_id, 3, start_offset, count),
                self._loop
            )
            return future.result(timeout=1.0)
        except Exception:
            return self._simdata.values[start_offset:start_offset + count]

    def set_register(self, offset: int, raw_value: int, client_ip: str = "127.0.0.1", is_external_write: bool = False) -> None:
        """Writes raw 16-bit register value to datastore (0-based offset)."""
        with self._lock:
            val = int(raw_value)
            if self._server and self._loop and self._is_running:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self._server.async_setValues(self.unit_id, 3, offset, [val]),
                        self._loop
                    )
                    future.result(timeout=1.0)
                except Exception:
                    if 0 <= offset < len(self._simdata.values):
                        self._simdata.values[offset] = val
            else:
                if 0 <= offset < len(self._simdata.values):
                    self._simdata.values[offset] = val

            self.transaction_count += 1
            self._window_trans_count += 1

            if is_external_write:
                meta = RegisterMap.METADATA.get(offset, {"name": f"REG_{offset}"})
                event = ModbusTransactionEvent(
                    timestamp=time.time(),
                    client_ip=client_ip,
                    function_code=6, # Preset Single Register
                    function_name="WriteSingleRegister",
                    register_address=40001 + offset,
                    register_name=meta.get("name", f"REG_{offset}"),
                    value=val,
                    is_write=True,
                )
                self.record_event(event)

    def record_event(self, event: ModbusTransactionEvent) -> None:
        """Appends a transaction event to the circular buffer."""
        self.event_buffer.append(event)
        if len(self.event_buffer) > self._max_buffer_size:
            self.event_buffer.pop(0)

    def update_request_rate(self) -> float:
        """Calculates instantaneous request rate (requests/sec)."""
        now = time.time()
        dt = now - self._last_rate_calc_time
        if dt >= 0.5:
            self.current_request_rate = round(self._window_trans_count / dt, 2)
            self._window_trans_count = 0
            self._last_rate_calc_time = now
        return self.current_request_rate

    def sync_from_process(
        self,
        tank_state: Dict[str, Any],
        setpoint: float,
        low_thresh: float,
        high_thresh: float,
        control_mode: int,
        alarm_state: int,
    ) -> None:
        """Synchronizes process and PLC state into the Modbus registers in one batch."""
        reg_values = [0] * 12
        reg_values[REG_TANK_LEVEL_SENSOR] = RegisterMap.to_raw(REG_TANK_LEVEL_SENSOR, tank_state["sensor_level"])
        reg_values[REG_SETPOINT_LEVEL]    = RegisterMap.to_raw(REG_SETPOINT_LEVEL, setpoint)
        reg_values[REG_PUMP_COMMAND]      = int(tank_state["pump_state"])
        reg_values[REG_VALVE_COMMAND]     = int(tank_state["valve_state"])
        reg_values[REG_INFLOW_RATE]       = RegisterMap.to_raw(REG_INFLOW_RATE, tank_state["sensor_inflow"])
        reg_values[REG_OUTFLOW_RATE]      = RegisterMap.to_raw(REG_OUTFLOW_RATE, tank_state["sensor_outflow"])
        reg_values[REG_ALARM_STATE]       = int(alarm_state)
        reg_values[REG_LOW_THRESHOLD]     = RegisterMap.to_raw(REG_LOW_THRESHOLD, low_thresh)
        reg_values[REG_HIGH_THRESHOLD]    = RegisterMap.to_raw(REG_HIGH_THRESHOLD, high_thresh)
        reg_values[REG_CONTROL_MODE]      = int(control_mode)
        reg_values[REG_TRUE_TANK_LEVEL]   = RegisterMap.to_raw(REG_TRUE_TANK_LEVEL, tank_state["true_level"])
        reg_values[REG_PHYSICAL_RESIDUAL] = RegisterMap.to_raw(REG_PHYSICAL_RESIDUAL, tank_state["residual"])

        if self._server and self._loop and self._is_running:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._server.async_setValues(self.unit_id, 3, 0, reg_values),
                    self._loop
                )
                future.result(timeout=1.0)
            except Exception:
                for i, v in enumerate(reg_values):
                    self._simdata.values[i] = v
        else:
            for i, v in enumerate(reg_values):
                self._simdata.values[i] = v

    def _run_server_thread(self) -> None:
        async def _async_main():
            self._loop = asyncio.get_running_loop()
            self._server = ModbusTcpServer(context=self._simdevice, address=(self.host, self.port))
            self._is_running = True
            self._ready_event.set()
            await self._server.serve_forever()

        asyncio.run(_async_main())

    def start(self) -> None:
        """Starts Modbus TCP server in background thread."""
        if not self._is_running:
            self._ready_event.clear()
            self._thread = threading.Thread(target=self._run_server_thread, name="ModbusServerThread", daemon=True)
            self._thread.start()
            self._ready_event.wait(timeout=2.0)
            time.sleep(0.3)

    def stop(self) -> None:
        """Gracefully shuts down Modbus TCP server."""
        if self._is_running:
            self._is_running = False
            if self._server and self._loop and self._loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(self._server.shutdown(), self._loop)
                    future.result(timeout=1.0)
                except Exception:
                    pass
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
                self._thread = None
