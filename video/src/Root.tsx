import { Composition } from "remotion";
import { OpenCMODemo, TOTAL_FRAMES } from "./OpenCMODemo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="OpenCMODemo"
      component={OpenCMODemo}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
