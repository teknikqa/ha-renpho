# Changelog

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
