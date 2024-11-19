PATH := ~/.solc-select/artifacts/:~/.solc-select/artifacts/solc-0.8.20:$(PATH)
certora-psm3 :; PATH=${PATH} certoraRun PSM3.conf$(if $(rule), --rule $(rule),)$(if $(results), --wait_for_results all,)
