import React from "react";
import { Composition, registerRoot } from "remotion";
import { BridgeShort, BRIDGE_FRAMES } from "./videos/bridge/Bridge";
import { PepsiShort, PepsiCaptions, PEPSI_FRAMES } from "./videos/pepsi/Pepsi";
import { SilverShort, SilverCaptions, SILVER_FRAMES } from "./videos/silver/Silver";
import { GlitchShort, GlitchCaptions, GLITCH_FRAMES } from "./videos/glitch/Glitch";

const Root: React.FC = () => (
  <>
    <Composition id="PepsiCaptions" component={PepsiCaptions} durationInFrames={PEPSI_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="GlitchShort" component={GlitchShort} durationInFrames={GLITCH_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="GlitchCaptions" component={GlitchCaptions} durationInFrames={GLITCH_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="SilverShort" component={SilverShort} durationInFrames={SILVER_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="SilverCaptions" component={SilverCaptions} durationInFrames={SILVER_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="PepsiShort" component={PepsiShort} durationInFrames={PEPSI_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="BridgeShort" component={BridgeShort} durationInFrames={BRIDGE_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
registerRoot(Root);
