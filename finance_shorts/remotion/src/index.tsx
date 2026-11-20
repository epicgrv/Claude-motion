import React from "react";
import { Composition, registerRoot } from "remotion";
import { BridgeShort, BRIDGE_FRAMES } from "./videos/bridge/Bridge";
import { PepsiShort, PEPSI_FRAMES } from "./videos/pepsi/Pepsi";

const Root: React.FC = () => (
  <>
    <Composition id="PepsiShort" component={PepsiShort} durationInFrames={PEPSI_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="BridgeShort" component={BridgeShort} durationInFrames={BRIDGE_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
registerRoot(Root);
