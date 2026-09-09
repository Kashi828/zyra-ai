const CHANNEL = process.env.ZYRA_RELEASE_CHANNEL || "beta";
function getReleaseInfo() { return { product:"ZYRA AI", channel:CHANNEL, supportedChannels:["beta","stable"], installerTarget:"win32-x64-nsis" }; }
module.exports = { getReleaseInfo };
