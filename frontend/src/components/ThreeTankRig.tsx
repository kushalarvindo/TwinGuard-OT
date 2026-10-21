import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { TelemetryFrame } from '../types';
import { RotateCw, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';

interface Props {
  frame: TelemetryFrame;
  height?: number | string;
}

export default function ThreeTankRig({ frame, height = 340 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animFrameId = useRef<number | null>(null);

  // Dynamic references updated every frame without tearing down scene
  const trueLevelRef = useRef<number>(frame.true_level);
  const sensorLevelRef = useRef<number>(frame.sensor_level);
  const pumpStateRef = useRef<number>(frame.pump_state);
  const valveStateRef = useRef<number>(frame.valve_state);
  const spoofedRef = useRef<boolean>(frame.sensor_spoofed);

  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<'perspective' | 'front' | 'top'>('perspective');

  // Keep refs synchronized with incoming telemetry
  useEffect(() => {
    trueLevelRef.current = frame.true_level;
    sensorLevelRef.current = frame.sensor_level;
    pumpStateRef.current = frame.pump_state;
    valveStateRef.current = frame.valve_state;
    spoofedRef.current = frame.sensor_spoofed;
  }, [frame]);

  // Handle auto-rotate state change on existing controls
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
      controlsRef.current.autoRotateSpeed = 1.2;
    }
  }, [autoRotate]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene & Cinematic Fog
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060913); // Deep industrial navy-slate
    scene.fog = new THREE.FogExp2(0x060913, 0.025);

    // 2. Camera Setup
    const width = container.clientWidth || 600;
    const heightPx = typeof height === 'number' ? height : container.clientHeight || 340;
    const camera = new THREE.PerspectiveCamera(42, width / heightPx, 0.1, 100);
    camera.position.set(0, 5.5, 12);

    // 3. Renderer with PBR Tonemapping & Shadows
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(width, heightPx);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Guard fill-rate
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.05; // Prevent camera from dipping underneath the floor
    controls.minDistance = 5;
    controls.maxDistance = 22;
    controls.target.set(0, 1.8, 0);
    controls.update();
    controlsRef.current = controls;

    // 5. Cinematic Moody Industrial Lighting
    const ambientLight = new THREE.AmbientLight(0x0d1527, 0.45);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0x1e293b, 0x090e17, 0.4);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xf8fafc, 1.9);
    keyLight.position.set(8, 14, 8);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(1024, 1024);
    keyLight.shadow.camera.near = 0.5;
    keyLight.shadow.camera.far = 30;
    keyLight.shadow.camera.left = -6;
    keyLight.shadow.camera.right = 6;
    keyLight.shadow.camera.top = 6;
    keyLight.shadow.camera.bottom = -6;
    keyLight.shadow.bias = -0.0005;
    scene.add(keyLight);

    const cyanRim = new THREE.SpotLight(0x38bdf8, 3.8, 30, Math.PI / 4, 0.8);
    cyanRim.position.set(-8, 10, -8);
    scene.add(cyanRim);

    const warmFill = new THREE.PointLight(0xf59e0b, 1.2, 18);
    warmFill.position.set(6, 1, -4);
    scene.add(warmFill);

    // 6. Industrial Floor & Pedestal Grid
    const floorGeo = new THREE.PlaneGeometry(30, 30);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x080d1a,
      roughness: 0.85,
      metalness: 0.2,
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.01;
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(24, 24, 0x1e293b, 0x0f172a);
    grid.position.y = 0;
    scene.add(grid);

    // Structural Base Plinth
    const plinthGeo = new THREE.BoxGeometry(9.6, 0.25, 4.4);
    const plinthMat = new THREE.MeshStandardMaterial({ color: 0x131c2e, roughness: 0.4, metalness: 0.8 });
    const plinth = new THREE.Mesh(plinthGeo, plinthMat);
    plinth.position.set(0, 0.125, 0);
    plinth.receiveShadow = true;
    scene.add(plinth);

    // 7. PBR Materials
    const glassMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transmission: 0.94,
      opacity: 0.35,
      transparent: true,
      roughness: 0.05,
      ior: 1.52,
      thickness: 0.4,
      specularIntensity: 1.0,
      specularColor: new THREE.Color(0xffffff),
      side: THREE.DoubleSide,
      depthWrite: false,
    });

    const steelMaterial = new THREE.MeshStandardMaterial({
      color: 0x475569,
      roughness: 0.28,
      metalness: 0.85,
    });

    const darkSteelMaterial = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.35,
      metalness: 0.9,
    });

    const brassMaterial = new THREE.MeshStandardMaterial({
      color: 0xd97706,
      roughness: 0.3,
      metalness: 0.8,
    });

    // Custom Liquid Shaders for Top Meniscus
    const createWaterSurfaceShader = (colorDeepHex: number, colorShallowHex: number) => {
      return new THREE.ShaderMaterial({
        uniforms: {
          uTime: { value: 0 },
          uColorDeep: { value: new THREE.Color(colorDeepHex) },
          uColorShallow: { value: new THREE.Color(colorShallowHex) },
          uWaveHeight: { value: 0.05 },
          uWaveSpeed: { value: 2.0 },
        },
        vertexShader: `
          uniform float uTime;
          uniform float uWaveHeight;
          uniform float uWaveSpeed;
          varying vec2 vUv;
          varying float vElevation;
          varying vec3 vNormal;

          void main() {
            vUv = uv;
            vec3 pos = position;
            float w1 = sin(pos.x * 5.0 + uTime * uWaveSpeed) * cos(pos.y * 5.0 + uTime * uWaveSpeed * 0.8);
            float w2 = sin(pos.x * 8.0 - uTime * 2.5) * 0.3;
            float elev = (w1 + w2) * uWaveHeight;
            pos.z += elev;
            vElevation = elev;
            vNormal = normal;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 uColorDeep;
          uniform vec3 uColorShallow;
          varying vec2 vUv;
          varying float vElevation;
          varying vec3 vNormal;

          void main() {
            float factor = clamp((vElevation + 0.06) * 4.0, 0.0, 1.0);
            vec3 col = mix(uColorDeep, uColorShallow, factor);
            gl_FragColor = vec4(col, 0.92);
          }
        `,
        transparent: true,
        side: THREE.DoubleSide,
      });
    };

    const surfaceShaderTrue = createWaterSurfaceShader(0x0284c7, 0x38bdf8);
    const surfaceShaderSensor = createWaterSurfaceShader(0x0f766e, 0x2dd4bf);

    // 8. Construct Tank Assembly Function
    const TANK_RADIUS = 1.05;
    const TANK_HEIGHT = 3.6;

    const buildTank = (xPos: number) => {
      const tankGroup = new THREE.Group();
      tankGroup.position.set(xPos, 0.25, 0);

      // Glass Outer Cylinder
      const cylinderGeo = new THREE.CylinderGeometry(TANK_RADIUS, TANK_RADIUS, TANK_HEIGHT, 36, 1, true);
      const glassCylinder = new THREE.Mesh(cylinderGeo, glassMaterial);
      glassCylinder.position.y = TANK_HEIGHT / 2;
      glassCylinder.castShadow = true;
      tankGroup.add(glassCylinder);

      // Top and Bottom Structural Collars
      const collarGeo = new THREE.CylinderGeometry(TANK_RADIUS * 1.06, TANK_RADIUS * 1.06, 0.12, 36);
      const bottomCollar = new THREE.Mesh(collarGeo, darkSteelMaterial);
      bottomCollar.position.y = 0.06;
      bottomCollar.castShadow = true;
      tankGroup.add(bottomCollar);

      const topCollar = new THREE.Mesh(collarGeo, darkSteelMaterial);
      topCollar.position.y = TANK_HEIGHT;
      topCollar.castShadow = true;
      tankGroup.add(topCollar);

      // Base Support Legs
      for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 2) {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.25, 0.12), steelMaterial);
        leg.position.set(Math.cos(angle) * (TANK_RADIUS * 0.9), -0.125, Math.sin(angle) * (TANK_RADIUS * 0.9));
        tankGroup.add(leg);
      }

      // Height Gauge Scale Bar & Marks
      const scaleBar = new THREE.Mesh(new THREE.BoxGeometry(0.04, TANK_HEIGHT, 0.04), brassMaterial);
      scaleBar.position.set(TANK_RADIUS + 0.12, TANK_HEIGHT / 2, 0);
      tankGroup.add(scaleBar);

      // Level Marker Rings (30% Low, 70% Setpoint, 80% High)
      const ringGeo = new THREE.TorusGeometry(TANK_RADIUS * 1.02, 0.015, 8, 36);
      
      const lowRingMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0284c7, emissiveIntensity: 0.6 });
      const lowRing = new THREE.Mesh(ringGeo, lowRingMat);
      lowRing.rotation.x = Math.PI / 2;
      lowRing.position.y = TANK_HEIGHT * 0.3;
      tankGroup.add(lowRing);

      const spRingMat = new THREE.MeshStandardMaterial({ color: 0x22c55e, emissive: 0x15803d, emissiveIntensity: 0.8 });
      const spRing = new THREE.Mesh(ringGeo, spRingMat);
      spRing.rotation.x = Math.PI / 2;
      spRing.position.y = TANK_HEIGHT * 0.7;
      tankGroup.add(spRing);

      const highRingMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xb45309, emissiveIntensity: 0.8 });
      const highRing = new THREE.Mesh(ringGeo, highRingMat);
      highRing.rotation.x = Math.PI / 2;
      highRing.position.y = TANK_HEIGHT * 0.8;
      tankGroup.add(highRing);

      // Water Cylinder Mesh (PBR Physical Liquid)
      const waterMat = new THREE.MeshPhysicalMaterial({
        color: 0x0ea5e9,
        metalness: 0.02,
        roughness: 0.1,
        transmission: 0.82,
        ior: 1.333,
        thickness: 1.8,
        transparent: true,
        opacity: 0.88,
        depthWrite: false,
      });

      // 1 unit high unit cylinder, scaled dynamically in render loop
      const waterGeo = new THREE.CylinderGeometry(TANK_RADIUS * 0.96, TANK_RADIUS * 0.96, 1, 32);
      waterGeo.translate(0, 0.5, 0); // Origin at base
      const waterMesh = new THREE.Mesh(waterGeo, waterMat);
      waterMesh.position.y = 0.01;
      tankGroup.add(waterMesh);

      // Water Top Surface Cap (Wave shader)
      const capGeo = new THREE.CircleGeometry(TANK_RADIUS * 0.95, 32);
      const capMesh = new THREE.Mesh(capGeo, xPos < 0 ? surfaceShaderTrue : surfaceShaderSensor);
      capMesh.rotation.x = -Math.PI / 2;
      tankGroup.add(capMesh);

      scene.add(tankGroup);

      return { tankGroup, waterMesh, capMesh, waterMat };
    };

    // Instantiate Dual Tanks: Left = True Physical, Right = Sensor Reported
    const trueTank = buildTank(-2.2);
    const sensorTank = buildTank(2.2);

    // 9. Process Interconnection Piping & Actuators
    const pipeMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.35, metalness: 0.85 });
    
    // Inflow Pump Housing (Mounted on left plinth)
    const pumpGroup = new THREE.Group();
    pumpGroup.position.set(-4.2, 0.5, 0);

    const pumpBody = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.6, 24), darkSteelMaterial);
    pumpBody.rotation.z = Math.PI / 2;
    pumpGroup.add(pumpBody);

    const pumpImpeller = new THREE.Mesh(
      new THREE.TorusGeometry(0.24, 0.06, 8, 16),
      new THREE.MeshStandardMaterial({ color: 0x22c55e, emissive: 0x22c55e, emissiveIntensity: 0.5 })
    );
    pumpGroup.add(pumpImpeller);
    scene.add(pumpGroup);

    // Inflow Overhead Pipe from Pump to True Tank Top
    const inletPipeCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-4.2, 0.8, 0),
      new THREE.Vector3(-4.2, 3.9, 0),
      new THREE.Vector3(-2.2, 3.9, 0),
      new THREE.Vector3(-2.2, 3.65, 0),
    ]);
    const inletPipe = new THREE.Mesh(new THREE.TubeGeometry(inletPipeCurve, 24, 0.08, 12, false), pipeMat);
    scene.add(inletPipe);

    // Effluent Discharge Valve Assembly (Mounted on right plinth)
    const valveGroup = new THREE.Group();
    valveGroup.position.set(4.2, 0.45, 0);

    const valveBody = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.4), darkSteelMaterial);
    valveGroup.add(valveBody);

    const valveHandwheel = new THREE.Mesh(
      new THREE.TorusGeometry(0.18, 0.03, 8, 16),
      new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x0284c7, emissiveIntensity: 0.4 })
    );
    valveHandwheel.rotation.x = Math.PI / 2;
    valveHandwheel.position.y = 0.28;
    valveGroup.add(valveHandwheel);
    scene.add(valveGroup);

    // Discharge Pipe from Tank Bottom to Valve
    const outletPipeCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(2.2, 0.35, 0),
      new THREE.Vector3(4.2, 0.35, 0),
      new THREE.Vector3(4.6, 0.35, 0),
    ]);
    const outletPipe = new THREE.Mesh(new THREE.TubeGeometry(outletPipeCurve, 16, 0.08, 12, false), pipeMat);
    scene.add(outletPipe);

    // 10. Responsive Canvas Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: newW, height: newH } = entry.contentRect;
        if (newW > 0 && newH > 0) {
          camera.aspect = newW / newH;
          camera.updateProjectionMatrix();
          renderer.setSize(newW, newH);
        }
      }
    });
    resizeObserver.observe(container);

    // 11. Render Loop with Smooth Spring Interpolation
    const clock = new THREE.Clock();
    let currentTrueHeight = frame.true_level;
    let currentSensorHeight = frame.sensor_level;

    const animate = () => {
      animFrameId.current = requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const time = clock.getElapsedTime();

      // Smooth liquid interpolation
      const targetTrue = Math.max(1, Math.min(100, trueLevelRef.current));
      const targetSensor = Math.max(1, Math.min(100, sensorLevelRef.current));

      currentTrueHeight += (targetTrue - currentTrueHeight) * 0.08;
      currentSensorHeight += (targetSensor - currentSensorHeight) * 0.08;

      const scaleTrue = (currentTrueHeight / 100) * (TANK_HEIGHT * 0.98);
      const scaleSensor = (currentSensorHeight / 100) * (TANK_HEIGHT * 0.98);

      // Scale water cylinders
      trueTank.waterMesh.scale.set(1, scaleTrue, 1);
      trueTank.capMesh.position.y = scaleTrue + 0.01;

      sensorTank.waterMesh.scale.set(1, scaleSensor, 1);
      sensorTank.capMesh.position.y = scaleSensor + 0.01;

      // Update surface shaders
      surfaceShaderTrue.uniforms.uTime.value = time;
      surfaceShaderTrue.uniforms.uWaveSpeed.value = pumpStateRef.current === 1 ? 3.5 : 0.8;
      surfaceShaderTrue.uniforms.uWaveHeight.value = pumpStateRef.current === 1 ? 0.06 : 0.02;

      surfaceShaderSensor.uniforms.uTime.value = time;

      // Color reaction when sensor is spoofed or diverged
      const isSpoofed = spoofedRef.current || Math.abs(currentTrueHeight - currentSensorHeight) > 5.0;
      if (isSpoofed) {
        sensorTank.waterMat.color.setHex(0xef4444); // Alert Crimson
        surfaceShaderSensor.uniforms.uColorDeep.value.setHex(0xb91c1c);
        surfaceShaderSensor.uniforms.uColorShallow.value.setHex(0xf87171);
      } else {
        sensorTank.waterMat.color.setHex(0x0f766e); // Synchronized Teal
        surfaceShaderSensor.uniforms.uColorDeep.value.setHex(0x0f766e);
        surfaceShaderSensor.uniforms.uColorShallow.value.setHex(0x2dd4bf);
      }

      // Impeller rotation when pump energized
      if (pumpStateRef.current === 1) {
        pumpImpeller.rotation.z += 12 * delta;
        pumpImpeller.material.emissiveIntensity = 0.8 + Math.sin(time * 10) * 0.4;
      } else {
        pumpImpeller.material.emissiveIntensity = 0.1;
      }

      // Valve state indicator
      if (valveStateRef.current === 1) {
        valveHandwheel.material.color.setHex(0x22c55e);
        valveHandwheel.material.emissive.setHex(0x16a34a);
        valveHandwheel.material.emissiveIntensity = 0.8;
      } else {
        valveHandwheel.material.color.setHex(0x64748b);
        valveHandwheel.material.emissive.setHex(0x1e293b);
        valveHandwheel.material.emissiveIntensity = 0.2;
      }

      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    // 12. Cleanup on Unmount
    return () => {
      resizeObserver.disconnect();
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);

      scene.traverse((child: any) => {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
          if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
          else child.material.dispose();
        }
      });
      renderer.dispose();
    };
  }, [height]);

  const switchCameraView = (view: 'perspective' | 'front' | 'top') => {
    setActiveView(view);
    if (!controlsRef.current) return;
    const controls = controlsRef.current;
    if (view === 'perspective') {
      controls.object.position.set(0, 5.5, 12);
      controls.target.set(0, 1.8, 0);
    } else if (view === 'front') {
      controls.object.position.set(0, 2.0, 11);
      controls.target.set(0, 1.8, 0);
    } else if (view === 'top') {
      controls.object.position.set(0, 13, 0.1);
      controls.target.set(0, 1.8, 0);
    }
    controls.update();
  };

  const delta = Math.abs(frame.true_level - frame.sensor_level);
  const isDiverged = delta > 5.0 || frame.sensor_spoofed;

  return (
    <div className="three-scene-container" style={{ position: 'relative', width: '100%', height }}>
      {/* 3D WebGL Canvas Target */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', borderRadius: 10, overflow: 'hidden' }} />

      {/* Floating HUD Viewport Bar */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            background: 'rgba(6, 9, 19, 0.75)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255,255,255,0.1)',
            padding: '3px 8px',
            borderRadius: 6,
            fontSize: 10,
            fontFamily: "'JetBrains Mono', monospace",
            fontWeight: 700,
            color: 'var(--text-secondary)',
          }}
        >
          <Sparkles size={11} style={{ color: 'var(--color-blue)' }} />
          <span>WEBGL 3D DIGITAL TWIN RIG</span>
        </div>

        <button
          className="btn-sm"
          onClick={() => setAutoRotate(!autoRotate)}
          style={{
            background: autoRotate ? 'rgba(56, 189, 248, 0.25)' : 'rgba(6, 9, 19, 0.75)',
            backdropFilter: 'blur(8px)',
            border: `1px solid ${autoRotate ? 'var(--color-blue)' : 'rgba(255,255,255,0.1)'}`,
            color: autoRotate ? 'var(--color-blue)' : 'var(--text-secondary)',
            height: 24,
            padding: '0 8px',
            fontSize: 10,
          }}
        >
          <RotateCw size={11} className={autoRotate ? 'spin' : ''} />
          <span>{autoRotate ? 'Orbiting' : 'Rotate'}</span>
        </button>

        <div style={{ display: 'flex', gap: 2 }}>
          <button
            className="btn-sm"
            onClick={() => switchCameraView('perspective')}
            style={{
              background: activeView === 'perspective' ? 'rgba(56, 189, 248, 0.25)' : 'rgba(6, 9, 19, 0.75)',
              border: `1px solid ${activeView === 'perspective' ? 'var(--color-blue)' : 'rgba(255,255,255,0.1)'}`,
              color: activeView === 'perspective' ? 'var(--color-blue)' : 'var(--text-secondary)',
              height: 24,
              padding: '0 6px',
              fontSize: 10,
            }}
            title="Perspective Orbit View"
          >
            3D Orbit
          </button>
          <button
            className="btn-sm"
            onClick={() => switchCameraView('front')}
            style={{
              background: activeView === 'front' ? 'rgba(56, 189, 248, 0.25)' : 'rgba(6, 9, 19, 0.75)',
              border: `1px solid ${activeView === 'front' ? 'var(--color-blue)' : 'rgba(255,255,255,0.1)'}`,
              color: activeView === 'front' ? 'var(--color-blue)' : 'var(--text-secondary)',
              height: 24,
              padding: '0 6px',
              fontSize: 10,
            }}
            title="Front Elevation View"
          >
            Front
          </button>
          <button
            className="btn-sm"
            onClick={() => switchCameraView('top')}
            style={{
              background: activeView === 'top' ? 'rgba(56, 189, 248, 0.25)' : 'rgba(6, 9, 19, 0.75)',
              border: `1px solid ${activeView === 'top' ? 'var(--color-blue)' : 'rgba(255,255,255,0.1)'}`,
              color: activeView === 'top' ? 'var(--color-blue)' : 'var(--text-secondary)',
              height: 24,
              padding: '0 6px',
              fontSize: 10,
            }}
            title="Top Plan View"
          >
            Top
          </button>
        </div>
      </div>

      {/* Floating State Indicators at Bottom */}
      <div
        style={{
          position: 'absolute',
          bottom: 10,
          left: 12,
          right: 12,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Left Ground Truth Tag */}
        <div
          style={{
            background: 'rgba(6, 9, 19, 0.8)',
            backdropFilter: 'blur(6px)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: 6,
            padding: '4px 10px',
            fontSize: 10,
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          <div style={{ color: 'var(--text-muted)', fontSize: 9 }}>GROUND TRUTH TANK</div>
          <div style={{ color: 'var(--color-blue)', fontWeight: 800, fontSize: 13 }}>
            {frame.true_level.toFixed(1)}%
          </div>
        </div>

        {/* Center Divergence Badge */}
        <div
          style={{
            background: isDiverged ? 'rgba(239, 68, 68, 0.85)' : 'rgba(15, 23, 42, 0.8)',
            backdropFilter: 'blur(8px)',
            border: `1px solid ${isDiverged ? 'rgba(239, 68, 68, 0.6)' : 'rgba(56, 189, 248, 0.3)'}`,
            borderRadius: 9999,
            padding: '4px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 10,
            fontWeight: 700,
            fontFamily: "'JetBrains Mono', monospace",
            color: '#fff',
            boxShadow: isDiverged ? '0 0 16px rgba(239, 68, 68, 0.4)' : 'none',
          }}
        >
          {isDiverged ? <ShieldAlert size={12} /> : <CheckCircle2 size={12} style={{ color: '#4ade80' }} />}
          <span>{isDiverged ? `DIVERGENCE Δ = ${delta.toFixed(2)}%` : `SYNCHRONIZED Δ = ${delta.toFixed(2)}%`}</span>
        </div>

        {/* Right Sensor Readout Tag */}
        <div
          style={{
            background: 'rgba(6, 9, 19, 0.8)',
            backdropFilter: 'blur(6px)',
            border: `1px solid ${isDiverged ? 'rgba(239, 68, 68, 0.4)' : 'rgba(45, 212, 191, 0.3)'}`,
            borderRadius: 6,
            padding: '4px 10px',
            fontSize: 10,
            fontFamily: "'JetBrains Mono', monospace",
            textAlign: 'right',
          }}
        >
          <div style={{ color: 'var(--text-muted)', fontSize: 9 }}>REPORTED SENSOR</div>
          <div
            style={{
              color: isDiverged ? 'var(--color-red)' : 'var(--color-teal)',
              fontWeight: 800,
              fontSize: 13,
            }}
          >
            {frame.sensor_level.toFixed(1)}%
            {frame.sensor_spoofed && <span style={{ fontSize: 9, marginLeft: 4, color: '#f87171' }}>[SPOOFED]</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
