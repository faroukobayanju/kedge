import { Composition, continueRender, delayRender, staticFile } from "remotion";
import { Film, DURATION } from "./kedge/Film";

// self-hosted Kedge fonts (kedge/ui/fonts), loaded before any frame renders
const faces: [string, string, string][] = [
  ["Archivo", "Archivo-400.woff2", "400"], ["Archivo", "Archivo-600.woff2", "600"], ["Archivo", "Archivo-800.woff2", "800"], ["Archivo", "Archivo-900.woff2", "900"],
  ["Permanent Marker", "PermanentMarker-400.woff2", "400"], ["JetBrains Mono", "JetBrainsMono-400.woff2", "400"], ["JetBrains Mono", "JetBrainsMono-600.woff2", "600"],
];
if (typeof document !== "undefined") {
  const handle = delayRender("fonts");
  Promise.all(faces.map(([family, file, weight]) => new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, { weight }).load().then((f) => document.fonts.add(f))))
    .then(() => continueRender(handle));
}

export const Root = () => (
  <Composition id="Kedge" component={Film} width={1920} height={1080} fps={30} durationInFrames={Math.round(DURATION * 30)}
    defaultProps={{ fps: 30 }} calculateMetadata={({ props }) => { const fps = props.fps || 30; return { fps, durationInFrames: Math.round(DURATION * fps) }; }} />
);
