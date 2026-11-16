# Changelog

## [0.1.2](https://github.com/teknikqa/ha-renpho/compare/v0.1.1...v0.1.2) (2026-11-16)


### Features

* add a diagnostics download ([440497d](https://github.com/teknikqa/ha-renpho/commit/440497de509cff05a21a4a7bc0f8c41595642880))
* add a diagnostics download ([a2c18d3](https://github.com/teknikqa/ha-renpho/commit/a2c18d3ac0fca527a6b714f913b298fca23e8fb4))
* let the poll interval be set from 5 minutes to 24 hours ([05169ed](https://github.com/teknikqa/ha-renpho/commit/05169edb31843dfb9937d12baa7f05a09139e7c9))
* let the poll interval be set from 5 minutes to 24 hours ([f4934e2](https://github.com/teknikqa/ha-renpho/commit/f4934e28312e2d3f0ad8aaf39c521953e5cb2634))
* reuse the saved session token across restarts ([067f08c](https://github.com/teknikqa/ha-renpho/commit/067f08c794f198c22126663b695bc446c2122f03))
* reuse the saved session token across restarts ([dcf5b5a](https://github.com/teknikqa/ha-renpho/commit/dcf5b5a326cb40d91729dfcb41f5e17f7205f1cc))

## [0.1.1](https://github.com/teknikqa/ha-renpho/compare/v0.1.0...v0.1.1) (2026-11-16)


### Bug Fixes

* log the server's login error and tell a refusal from a network failure ([ddce3bc](https://github.com/teknikqa/ha-renpho/commit/ddce3bcc0ca583f879f5042b1a905ef42621404a))
* login works again (send app version) and server errors are shown ([e4bfb74](https://github.com/teknikqa/ha-renpho/commit/e4bfb74046bf75d2f2ef6cd5672573f72725fda6))
* only known bad-password codes count as invalid credentials ([1915a9e](https://github.com/teknikqa/ha-renpho/commit/1915a9e4fd6d1d3e3778a23fa083733ad529a747))
* only known bad-password codes count as invalid credentials ([83c59a9](https://github.com/teknikqa/ha-renpho/commit/83c59a9c32053319821ee6df89d48959162af034))
* read every page of measurements so sensors show the newest weigh-in ([902a9b4](https://github.com/teknikqa/ha-renpho/commit/902a9b46c03bb2f6bf7e73ce6436c989511f2527))
* read every page of measurements so sensors show the newest weigh-in ([c29e52f](https://github.com/teknikqa/ha-renpho/commit/c29e52ff9c5f369008b9d0aa0de12ae2598ed0df)), closes [#1](https://github.com/teknikqa/ha-renpho/issues/1)
* send the app version on login so the server can decrypt it ([2406c3d](https://github.com/teknikqa/ha-renpho/commit/2406c3d686ac0bacec7dbff13376a076b15d35bc)), closes [#2](https://github.com/teknikqa/ha-renpho/issues/2)
* show the server's login error and stop calling decrypt failures a bad password ([a0213ad](https://github.com/teknikqa/ha-renpho/commit/a0213ad38979bcd848c8383dcdbe21e7915f3464)), closes [#2](https://github.com/teknikqa/ha-renpho/issues/2)
