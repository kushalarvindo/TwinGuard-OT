declare module 'three' {
  export const Color: any;
  export const Scene: any;
  export const PerspectiveCamera: any;
  export const WebGLRenderer: any;
  export const AmbientLight: any;
  export const DirectionalLight: any;
  export const PointLight: any;
  export const SpotLight: any;
  export const HemisphereLight: any;
  export const CylinderGeometry: any;
  export const BoxGeometry: any;
  export const SphereGeometry: any;
  export const PlaneGeometry: any;
  export const CircleGeometry: any;
  export const TubeGeometry: any;
  export const TorusGeometry: any;
  export const RingGeometry: any;
  export const MeshPhysicalMaterial: any;
  export const MeshStandardMaterial: any;
  export const MeshBasicMaterial: any;
  export const ShaderMaterial: any;
  export const Mesh: any;
  export const Group: any;
  export const Vector3: any;
  export const Vector2: any;
  export const Matrix4: any;
  export const CatmullRomCurve3: any;
  export const DoubleSide: any;
  export const FrontSide: any;
  export const BackSide: any;
  export const PCFSoftShadowMap: any;
  export const ACESFilmicToneMapping: any;
  export const Clock: any;
  export const FogExp2: any;
  export const GridHelper: any;
  export const InstancedMesh: any;
  export const Raycaster: any;
  const other: Record<string, any>;
  export default other;
}

declare module 'three/addons/controls/OrbitControls.js' {
  export class OrbitControls {
    constructor(camera: any, domElement: any);
    enableDamping: boolean;
    dampingFactor: number;
    maxPolarAngle: number;
    minPolarAngle: number;
    minDistance: number;
    maxDistance: number;
    autoRotate: boolean;
    autoRotateSpeed: number;
    target: any;
    object: any;
    update(): void;
    dispose(): void;
  }
}
