#!/usr/bin/env node

import Manager from "./index.js";

const host = {
  zjut: "192.168.210.175",
};

async function main() {
  try {
    const manager = new Manager({ host: "http://" + host[process.argv[2]] });
    await manager.logout();
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await manager.login();

    const status = await manager.check();
    if (status.error !== "ok") await manager.login();
  } catch (e) {
    process.exit(-1);
  }
}

main();
