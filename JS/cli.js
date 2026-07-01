#!/usr/bin/env node

import Manager from "./index.js";

const host = {
  zjut: "192.168.210.175",
  zjutpf: "192.168.210.171",
};

async function main() {
  try {
    const manager = process.argv[2] && host[process.argv[2]]
      ? new Manager({ host: "http://" + host[process.argv[2]] })
      : new Manager();
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
