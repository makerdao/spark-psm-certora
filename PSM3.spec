// PSM3.spec

using MockRateProvider as rateProvider;
using USDCMock as usdc;
using USDSMock as usds;
using SUSDSMock as susds;

methods {
    // storage variables
    function owner() external returns (address) envfree;
    function pocket() external returns (address) envfree;
    function totalShares() external returns (uint256) envfree;
    function shares(address) external returns (uint256) envfree;
    // immutables
    function usdc() external returns (address) envfree;
    function usds() external returns (address) envfree;
    function susds() external returns (address) envfree;
    function rateProvider() external returns (address) envfree;
    // getters
    function convertToAssets(address,uint256) external returns (uint256) envfree;
    function convertToAssetValue(uint256) external returns (uint256) envfree;
    function convertToShares(uint256) external returns (uint256) envfree;
    function convertToShares(address,uint256) external returns (uint256) envfree;
    function totalAssets() external returns (uint256) envfree;
    //
    function rateProvider.getConversionRate() external returns (uint256) envfree;
    function usdc.decimals() external returns (uint256) envfree;
    function usdc.allowance(address,address) external returns (uint256) envfree;
    function usdc.balanceOf(address) external returns (uint256) envfree;
    function usdc.totalSupply() external returns (uint256) envfree;
    function usds.decimals() external returns (uint256) envfree;
    function usds.balanceOf(address) external returns (uint256) envfree;
    function susds.decimals() external returns (uint256) envfree;
    function susds.balanceOf(address) external returns (uint256) envfree;
    //
    function _.decimals() external => DISPATCHER(true);
    function _.allowance(address,address) external => DISPATCHER(true);
    function _.balanceOf(address) external => DISPATCHER(true);
    function _.totalSupply() external => DISPATCHER(true);
    function _.transfer(address,uint256) external => DISPATCHER(true);
    function _.transferFrom(address,address,uint256) external => DISPATCHER(true);
    function _.getConversionRate() external => DISPATCHER(true);
    // function _.ceilDiv(uint256 a, uint256 b) internal => ceilDivSummary(a,b) expect uint256;
}

// function ceilDivSummary(uint256 a, uint256 b) returns uint256 {
//     require b > 0;
//     uint256 z = require_uint256(a / b);
//     return a % b > 0 ? require_uint256(z + 1) : z;
// }

definition defGetAssetCustodian(address asset) returns address = asset == usdc ? pocket() : currentContract;
definition defCeilDiv(mathint a, mathint b) returns mathint = a == 0 ? 0 : (a - 1) / b + 1;
definition defGetUsdcValue(mathint amount) returns mathint = amount * 10^18 / currentContract._usdcPrecision;
definition defGetUsdsValue(mathint amount) returns mathint = amount * 10^18 / currentContract._usdsPrecision;
definition defGetSUsdsValue(mathint amount, bool roundUp)
returns mathint = !roundUp ? amount * rateProvider.getConversionRate() / 10^9 / currentContract._susdsPrecision
                           : defCeilDiv(defCeilDiv(amount * rateProvider.getConversionRate(), 10^9), currentContract._susdsPrecision);
definition defGetAssetValue(address asset, mathint amount, bool roundUp)
returns mathint = asset == usdc ? defGetUsdcValue(amount)
                                : asset == usds ? defGetUsdsValue(amount)
                                                : defGetSUsdsValue(amount, roundUp);
definition defTotalAssets()
returns mathint = defGetUsdcValue(usdc.balanceOf(pocket())) +
                  defGetUsdsValue(usds.balanceOf(currentContract)) +
                  defGetSUsdsValue(susds.balanceOf(currentContract), false);
definition defConvertToShares(mathint assetValue)
returns mathint = defTotalAssets() == 0 ? assetValue
                                        : assetValue * totalShares() / defTotalAssets();
definition defConvertToSUsds(mathint amount, mathint assetPrecision, bool roundUp)
returns mathint = rateProvider.getConversionRate() == 0 ? 0 :
                  !roundUp ? amount * 10^27 / rateProvider.getConversionRate() * currentContract._susdsPrecision / assetPrecision
                           : defCeilDiv(defCeilDiv(amount * 10^27, rateProvider.getConversionRate()) * currentContract._susdsPrecision, assetPrecision);
definition defConvertFromSUsds(mathint amount, mathint assetPrecision, bool roundUp)
returns mathint = !roundUp ? amount * rateProvider.getConversionRate() / 10^27 * assetPrecision / currentContract._susdsPrecision
                           : defCeilDiv(defCeilDiv(amount * rateProvider.getConversionRate(), 10^27) * assetPrecision, currentContract._susdsPrecision);
definition defConvertOneToOne(mathint amount, mathint assetPrecision, mathint convertAssetPrecision, bool roundUp)
returns mathint = !roundUp ? amount * convertAssetPrecision / assetPrecision
                           : defCeilDiv(amount * convertAssetPrecision, assetPrecision);
definition defConvertToSharesRoundUp(mathint assetValue)
returns mathint = defTotalAssets() == 0 ? assetValue
                                        : defCeilDiv(assetValue * totalShares(), defTotalAssets());
definition defGetSwapQuote(address asset, address quoteAsset, mathint amount, bool roundUp)
returns mathint = (asset == usdc  && quoteAsset == usds  ? defConvertOneToOne(amount, currentContract._usdcPrecision, currentContract._usdsPrecision, roundUp) : 0) +
                  (asset == usdc  && quoteAsset == susds ? defConvertToSUsds(amount, currentContract._usdcPrecision, roundUp) : 0) +
                  (asset == usds  && quoteAsset == usdc  ? defConvertOneToOne(amount, currentContract._usdsPrecision, currentContract._usdcPrecision, roundUp) : 0) +
                  (asset == usds  && quoteAsset == susds ? defConvertToSUsds(amount, currentContract._usdsPrecision, roundUp) : 0) +
                  (asset == susds && quoteAsset == usdc  ? defConvertFromSUsds(amount, currentContract._usdcPrecision, roundUp) : 0) +
                  (asset == susds && quoteAsset == usds  ? defConvertFromSUsds(amount, currentContract._usdsPrecision, roundUp) : 0);
definition defConvertToAssetValue(mathint numShares)
returns mathint = totalShares() == 0 ? numShares
                                     : numShares * defTotalAssets() / totalShares();
definition defConvertToAssets(address asset, mathint numShares)
returns mathint = (asset == usdc  ? defConvertToAssetValue(numShares) * currentContract._usdcPrecision / 10^18 : 0) +
                  (asset == usds  ? defConvertToAssetValue(numShares) * currentContract._usdsPrecision / 10^18 : 0) +
                  (asset == susds ? defConvertToAssetValue(numShares) * 10^9 * currentContract._susdsPrecision / rateProvider.getConversionRate() : 0);


// returns mathint = asset == usdc  ? quoteAsset == usds  ? defConvertOneToOne(amount, currentContract._usdcPrecision, currentContract._usdsPrecision, roundUp)
//                                  : quoteAsset == susds ? defConvertToSUsds(amount, currentContract._usdcPrecision, roundUp) : 0
//                 : asset == usds  ? quoteAsset == usdc  ? defConvertOneToOne(amount, currentContract._usdsPrecision, currentContract._usdcPrecision, roundUp)
//                                  : quoteAsset == susds ? defConvertToSUsds(amount, currentContract._usdsPrecision, roundUp) : 0
//                 : asset == susds ? quoteAsset == usdc  ? defConvertFromSUsds(amount, currentContract._usdcPrecision, roundUp)
//                                  : quoteAsset == usds  ? defConvertFromSUsds(amount, currentContract._usdsPrecision, roundUp) : 0 : 0;

ghost sharesSum() returns mathint {
    init_state axiom sharesSum() == 0;
}

hook Sload uint256 share shares[KEY address a] {
    require sharesSum() >= to_mathint(share);
}

hook Sstore shares[KEY address a] uint256 share (uint256 old_share) {
    havoc sharesSum assuming sharesSum@new() == sharesSum@old() + share - old_share && sharesSum@new() >= 0;
}

invariant sharesSum_equals_totalShares() sharesSum() == to_mathint(totalShares());

// Verify no more entry points exist
rule entryPoints(method f) filtered { f -> !f.isView } {
    env e;

    calldataarg args;
    f(e, args);

    assert f.selector == sig:renounceOwnership().selector ||
           f.selector == sig:transferOwnership(address).selector ||
           f.selector == sig:setPocket(address).selector ||
           f.selector == sig:swapExactIn(address,address,uint256,uint256,address,uint256).selector ||
           f.selector == sig:swapExactOut(address,address,uint256,uint256,address,uint256).selector ||
           f.selector == sig:deposit(address,address,uint256).selector ||
           f.selector == sig:withdraw(address,address,uint256).selector;
}

// Verify that each storage layout is only modified in the corresponding functions
rule storageAffected(method f) {
    env e;

    address anyAddr;

    address ownerBefore = owner();
    address pocketBefore = pocket();
    mathint totalSharesBefore = totalShares();
    mathint sharesBefore = shares(anyAddr);

    calldataarg args;
    f(e, args);

    address ownerAfter = owner();
    address pocketAfter = pocket();
    mathint totalSharesAfter = totalShares();
    mathint sharesAfter = shares(anyAddr);

    assert ownerAfter != ownerBefore => f.selector == sig:renounceOwnership().selector || f.selector == sig:transferOwnership(address).selector, "Assert 1";
    assert pocketAfter != pocketBefore => f.selector == sig:setPocket(address).selector, "Assert 2";
    assert totalSharesAfter != totalSharesBefore => f.selector == sig:deposit(address,address,uint256).selector || f.selector == sig:withdraw(address,address,uint256).selector, "Assert 3";
    assert sharesAfter != sharesBefore => f.selector == sig:deposit(address,address,uint256).selector || f.selector == sig:withdraw(address,address,uint256).selector, "Assert 4";
}

// Verify correct storage changes for non reverting renounceOwnership
rule renounceOwnership() {
    env e;

    renounceOwnership(e);

    address ownerAfter = owner();

    assert ownerAfter == 0, "Assert 1";
}

// Verify revert rules on renounceOwnership
rule renounceOwnership_revert() {
    env e;

    address owner = owner();

    renounceOwnership@withrevert(e);

    bool revert1 = e.msg.value > 0;
    bool revert2 = owner != e.msg.sender;

    assert lastReverted <=> revert1 || revert2, "Revert rules failed";
}

// Verify correct storage changes for non reverting transferOwnership
rule transferOwnership(address newOwner) {
    env e;

    transferOwnership(e, newOwner);

    address ownerAfter = owner();

    assert ownerAfter == newOwner, "Assert 1";
}

// Verify revert rules on transferOwnership
rule transferOwnership_revert(address newOwner) {
    env e;

    address owner = owner();

    transferOwnership@withrevert(e, newOwner);

    bool revert1 = e.msg.value > 0;
    bool revert2 = owner != e.msg.sender;
    bool revert3 = newOwner == 0;

    assert lastReverted <=> revert1 || revert2 || revert3, "Revert rules failed";
}

// Verify correct storage changes for non reverting setPocket
rule setPocket(address newPocket) {
    env e;

    address oldPocket = pocket();
    mathint usdcBalanceOfOldPocketBefore = usdc.balanceOf(oldPocket);
    mathint usdcBalanceOfNewPocketBefore = usdc.balanceOf(newPocket);

    // ERC20 assumption
    require usdc.totalSupply() >= usdcBalanceOfOldPocketBefore + usdcBalanceOfNewPocketBefore;

    setPocket(e, newPocket);

    mathint usdcBalanceOfOldPocketAfter = usdc.balanceOf(oldPocket);
    mathint usdcBalanceOfNewPocketAfter = usdc.balanceOf(newPocket);
    address pocketAfter = pocket();

    assert usdcBalanceOfOldPocketAfter == 0, "Assert 1";
    assert usdcBalanceOfNewPocketAfter == usdcBalanceOfNewPocketBefore + usdcBalanceOfOldPocketBefore, "Assert 2";
    assert pocketAfter == newPocket, "Assert 3";

}

// Verify revert rules on setPocket
rule setPocket_revert(address newPocket) {
    env e;

    address owner = owner();
    address oldPocket = pocket();

    // Set up assumption
    require usdc.allowance(oldPocket, currentContract) == max_uint256;
    // ERC20 assumption
    require usdc.totalSupply() >= usdc.balanceOf(oldPocket) + usdc.balanceOf(newPocket);

    setPocket@withrevert(e, newPocket);

    bool revert1 = e.msg.value > 0;
    bool revert2 = owner != e.msg.sender;
    bool revert3 = newPocket == 0;
    bool revert4 = newPocket == oldPocket;

    assert lastReverted <=> revert1 || revert2 || revert3 ||
                            revert4, "Revert rules failed";
}

// Verify correct storage changes for non reverting swapExactIn
rule swapExactIn(address assetIn, address assetOut, uint256 amountIn, uint256 minAmountOut, address receiver, uint256 referralCode) {
    env e;

    require currentContract._usdcPrecision  == 10^8  &&
            currentContract._usdsPrecision  == 10^18 &&
            currentContract._susdsPrecision == 10^18;

    address custodianIn = defGetAssetCustodian(assetIn);
    address custodianOut = defGetAssetCustodian(assetOut);
    require e.msg.sender != custodianIn;
    address other;
    require other != e.msg.sender && other != custodianIn;
    address other2;
    require other2 != receiver && other2 != custodianOut;

    mathint amountOut = defGetSwapQuote(assetIn, assetOut, amountIn, false);

    mathint assetInBalanceOfSenderBefore = assetIn.balanceOf(e, e.msg.sender);
    mathint assetInBalanceOfCustodianBefore = assetIn.balanceOf(e, custodianIn);
    mathint assetInBalanceOfOtherBefore = assetIn.balanceOf(e, other);
    mathint assetOutBalanceOfReceiverBefore = assetOut.balanceOf(e, receiver);
    mathint assetOutBalanceOfCustodianBefore = assetOut.balanceOf(e, custodianOut);
    mathint assetOutBalanceOfOtherBefore = assetOut.balanceOf(e, other2);
    mathint totalAssetsBefore = totalAssets();

    // ERC20 assumption2
    require assetIn.totalSupply(e) >= assetInBalanceOfSenderBefore + assetInBalanceOfCustodianBefore + assetInBalanceOfOtherBefore;
    require assetOut.totalSupply(e) >= assetOutBalanceOfReceiverBefore + assetOutBalanceOfCustodianBefore + assetOutBalanceOfOtherBefore;

    mathint amountOutRet = swapExactIn(e, assetIn, assetOut, amountIn, minAmountOut, receiver, referralCode);

    mathint assetInBalanceOfSenderAfter = assetIn.balanceOf(e, e.msg.sender);
    mathint assetInBalanceOfCustodianAfter = assetIn.balanceOf(e, custodianIn);
    mathint assetInBalanceOfOtherAfter = assetIn.balanceOf(e, other);
    mathint assetOutBalanceOfReceiverAfter = assetOut.balanceOf(e, receiver);
    mathint assetOutBalanceOfCustodianAfter = assetOut.balanceOf(e, custodianOut);
    mathint assetOutBalanceOfOtherAfter = assetOut.balanceOf(e, other2);
    mathint totalAssetsAfter = totalAssets();

    assert amountOutRet == amountOut, "Assert 1";
    assert assetInBalanceOfSenderAfter == assetInBalanceOfSenderBefore - amountIn, "Assert 2";
    assert assetInBalanceOfCustodianAfter == assetInBalanceOfCustodianBefore + amountIn, "Assert 3";
    assert assetInBalanceOfOtherAfter == assetInBalanceOfOtherBefore, "Assert 4";
    assert receiver != custodianOut => assetOutBalanceOfReceiverAfter == assetOutBalanceOfReceiverBefore + amountOut, "Assert 5";
    assert receiver != custodianOut => assetOutBalanceOfCustodianAfter == assetOutBalanceOfCustodianBefore - amountOut, "Assert 6";
    assert receiver == custodianOut => assetOutBalanceOfReceiverAfter == assetOutBalanceOfReceiverBefore, "Assert 7"; 
    assert assetOutBalanceOfOtherAfter == assetOutBalanceOfOtherBefore, "Assert 8";
    assert totalAssetsAfter >= totalAssetsBefore, "Assert 9";
}

// Verify revert rules on swapExactIn
rule swapExactIn_revert(address assetIn, address assetOut, uint256 amountIn, uint256 minAmountOut, address receiver, uint256 referralCode) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    address custodianOut = defGetAssetCustodian(assetOut);

    mathint assetInBalanceOfSender = assetIn.balanceOf(e, e.msg.sender);
    mathint assetOutBalanceOfCustodian = assetOut.balanceOf(e, custodianOut);
    mathint conversionRate = rateProvider.getConversionRate();

    mathint amountOut = defGetSwapQuote(assetIn, assetOut, amountIn, false);

    // Practical assumptions
    require assetInBalanceOfSender >= amountIn;
    require assetIn.allowance(e, e.msg.sender, currentContract) >= amountIn;
    require assetIn != usdc || assetOut != usds || amountIn * currentContract._usdsPrecision <= max_uint256;
    require assetIn != usds || assetOut != usdc || amountIn * currentContract._usdcPrecision <= max_uint256;
    require assetOut != susds || conversionRate == 0 || amountIn * 10^27 <= max_uint256 && amountIn * 10^27 / conversionRate * currentContract._susdsPrecision <= max_uint256;
    require assetIn != susds || assetOut != usdc || amountIn * conversionRate <= max_uint256 && amountIn * conversionRate / 10^27 * currentContract._usdcPrecision <= max_uint256;
    require assetIn != susds || assetOut != usds || amountIn * conversionRate <= max_uint256 && amountIn * conversionRate / 10^27 * currentContract._usdsPrecision <= max_uint256;
    // Setup assumption
    require custodianOut == currentContract || assetOut.allowance(e, custodianOut, currentContract) == max_uint256;
    // ERC20 assumptions
    require assetIn.totalSupply(e) >= assetInBalanceOfSender + assetIn.balanceOf(e, defGetAssetCustodian(assetIn));
    require assetOut.totalSupply(e) >= assetOut.balanceOf(e, receiver) + assetOutBalanceOfCustodian;

    swapExactIn@withrevert(e, assetIn, assetOut, amountIn, minAmountOut, receiver, referralCode);

    bool revert1 = e.msg.value > 0;
    bool revert2 = amountIn == 0;
    bool revert3 = receiver == 0;
    bool revert4 = assetIn == assetOut || assetIn != usdc && assetIn != usds && assetIn != susds || assetOut != usdc && assetOut != usds && assetOut != susds;
    bool revert5 = assetOut == susds && conversionRate == 0;
    bool revert6 = amountOut < minAmountOut;
    bool revert7 = assetOutBalanceOfCustodian < amountOut;

    assert lastReverted <=> revert1 || revert2 || revert3 ||
                            revert4 || revert5 || revert6 ||
                            revert7, "Revert rules failed";
}

// Verify correct storage changes for non reverting swapExactOut
rule swapExactOut(address assetIn, address assetOut, uint256 amountOut, uint256 maxAmountIn, address receiver, uint256 referralCode) {
    env e;

    require currentContract._usdcPrecision  == 10^8  &&
            currentContract._usdsPrecision  == 10^18 &&
            currentContract._susdsPrecision == 10^18;

    address custodianIn = defGetAssetCustodian(assetIn);
    address custodianOut = defGetAssetCustodian(assetOut);
    require e.msg.sender != custodianIn;
    address other;
    require other != e.msg.sender && other != custodianIn;
    address other2;
    require other2 != receiver && other2 != custodianOut;

    mathint amountIn = defGetSwapQuote(assetOut, assetIn, amountOut, true);

    mathint assetInBalanceOfSenderBefore = assetIn.balanceOf(e, e.msg.sender);
    mathint assetInBalanceOfCustodianBefore = assetIn.balanceOf(e, custodianIn);
    mathint assetInBalanceOfOtherBefore = assetIn.balanceOf(e, other);
    mathint assetOutBalanceOfReceiverBefore = assetOut.balanceOf(e, receiver);
    mathint assetOutBalanceOfCustodianBefore = assetOut.balanceOf(e, custodianOut);
    mathint assetOutBalanceOfOtherBefore = assetOut.balanceOf(e, other2);
    mathint totalAssetsBefore = totalAssets();

    // ERC20 assumption2
    require assetIn.totalSupply(e) >= assetInBalanceOfSenderBefore + assetInBalanceOfCustodianBefore + assetInBalanceOfOtherBefore;
    require assetOut.totalSupply(e) >= assetOutBalanceOfReceiverBefore + assetOutBalanceOfCustodianBefore + assetOutBalanceOfOtherBefore;

    mathint amountInRet = swapExactOut(e, assetIn, assetOut, amountOut, maxAmountIn, receiver, referralCode);

    mathint assetInBalanceOfSenderAfter = assetIn.balanceOf(e, e.msg.sender);
    mathint assetInBalanceOfCustodianAfter = assetIn.balanceOf(e, custodianIn);
    mathint assetInBalanceOfOtherAfter = assetIn.balanceOf(e, other);
    mathint assetOutBalanceOfReceiverAfter = assetOut.balanceOf(e, receiver);
    mathint assetOutBalanceOfCustodianAfter = assetOut.balanceOf(e, custodianOut);
    mathint assetOutBalanceOfOtherAfter = assetOut.balanceOf(e, other2);
    mathint totalAssetsAfter = totalAssets();

    assert amountInRet == amountIn, "Assert 1";
    assert assetInBalanceOfSenderAfter == assetInBalanceOfSenderBefore - amountIn, "Assert 2";
    assert assetInBalanceOfCustodianAfter == assetInBalanceOfCustodianBefore + amountIn, "Assert 3";
    assert assetInBalanceOfOtherAfter == assetInBalanceOfOtherBefore, "Assert 4";
    assert receiver != custodianOut => assetOutBalanceOfReceiverAfter == assetOutBalanceOfReceiverBefore + amountOut, "Assert 5";
    assert receiver != custodianOut => assetOutBalanceOfCustodianAfter == assetOutBalanceOfCustodianBefore - amountOut, "Assert 6";
    assert receiver == custodianOut => assetOutBalanceOfReceiverAfter == assetOutBalanceOfReceiverBefore, "Assert 7"; 
    assert assetOutBalanceOfOtherAfter == assetOutBalanceOfOtherBefore, "Assert 8";
    assert totalAssetsAfter >= totalAssetsBefore, "Assert 9";
}

// Verify revert rules on swapExactOut
rule swapExactOut_revert(address assetIn, address assetOut, uint256 amountOut, uint256 maxAmountIn, address receiver, uint256 referralCode) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    address custodianOut = defGetAssetCustodian(assetOut);

    mathint assetInBalanceOfSender = assetIn.balanceOf(e, e.msg.sender);
    mathint assetOutBalanceOfCustodian = assetOut.balanceOf(e, custodianOut);
    mathint conversionRate = rateProvider.getConversionRate();

    mathint amountIn = defGetSwapQuote(assetOut, assetIn, amountOut, true);

    // Practical assumptions
    require assetInBalanceOfSender >= amountIn;
    require assetIn.allowance(e, e.msg.sender, currentContract) >= amountIn;
    require assetOut != usdc || assetIn != usds || amountOut * currentContract._usdsPrecision <= max_uint256;
    require assetOut != usds || assetIn != usdc || amountOut * currentContract._usdcPrecision <= max_uint256;
    require assetIn != susds || conversionRate == 0 || amountOut * 10^27 <= max_uint256 && defCeilDiv(amountOut * 10^27, conversionRate) * currentContract._susdsPrecision <= max_uint256;
    require assetOut != susds || assetIn != usdc || amountOut * conversionRate <= max_uint256 && defCeilDiv(amountOut * conversionRate, 10^27) * currentContract._usdcPrecision <= max_uint256;
    require assetOut != susds || assetIn != usds || amountOut * conversionRate <= max_uint256 && defCeilDiv(amountOut * conversionRate, 10^27) * currentContract._usdsPrecision <= max_uint256;
    // Setup assumption
    require custodianOut == currentContract || assetOut.allowance(e, custodianOut, currentContract) == max_uint256;
    // ERC20 assumptions
    require assetIn.totalSupply(e) >= assetInBalanceOfSender + assetIn.balanceOf(e, defGetAssetCustodian(assetIn));
    require assetOut.totalSupply(e) >= assetOut.balanceOf(e, receiver) + assetOutBalanceOfCustodian;

    swapExactOut@withrevert(e, assetIn, assetOut, amountOut, maxAmountIn, receiver, referralCode);

    bool revert1 = e.msg.value > 0;
    bool revert2 = amountOut == 0;
    bool revert3 = receiver == 0;
    bool revert4 = assetIn == assetOut || assetIn != usdc && assetIn != usds && assetIn != susds || assetOut != usdc && assetOut != usds && assetOut != susds;
    bool revert5 = assetIn == susds && conversionRate == 0;
    bool revert6 = amountIn > maxAmountIn;
    bool revert7 = assetOutBalanceOfCustodian < amountOut;

    assert lastReverted <=> revert1 || revert2 || revert3 ||
                            revert4 || revert5 || revert6 ||
                            revert7, "Revert rules failed";
}

// Verify correct storage changes for non reverting deposit
rule deposit(address asset, address receiver, uint256 assetsToDeposit) {
    env e;

    require currentContract._usdcPrecision  == 10^8  &&
            currentContract._usdsPrecision  == 10^18 &&
            currentContract._susdsPrecision == 10^18;

    // Testing
    require rateProvider.getConversionRate() == 1008531473972262740411849263;
    //

    address other;
    require other != receiver;
    address custodian = defGetAssetCustodian(asset);
    require e.msg.sender != custodian;
    address other2;
    require other2 != e.msg.sender && other2 != custodian;

    mathint assetBalanceOfSenderBefore = asset.balanceOf(e, e.msg.sender);
    mathint assetBalanceOfCustodianBefore = asset.balanceOf(e, custodian);
    mathint assetBalanceOfOtherBefore = asset.balanceOf(e, other2);
    mathint totalSharesBefore = totalShares();
    mathint sharesReceiverBefore = shares(receiver);
    mathint sharesOtherBefore = shares(other);
    mathint newShares = defConvertToShares(defGetAssetValue(asset, assetsToDeposit, false));
    mathint totalAssetsBefore = totalAssets();

    // ERC20 assumption
    require asset.totalSupply(e) >= assetBalanceOfSenderBefore + assetBalanceOfCustodianBefore + assetBalanceOfOtherBefore;

    mathint newSharesRet = deposit(e, asset, receiver, assetsToDeposit);

    mathint assetBalanceOfSenderAfter = asset.balanceOf(e, e.msg.sender);
    mathint assetBalanceOfCustodianAfter = asset.balanceOf(e, custodian);
    mathint assetBalanceOfOtherAfter = asset.balanceOf(e, other2);
    mathint totalSharesAfter = totalShares();
    mathint sharesReceiverAfter = shares(receiver);
    mathint sharesOtherAfter = shares(other);
    mathint totalAssetsAfter = totalAssets();

    assert newSharesRet == newShares, "Assert 1";
    assert assetBalanceOfSenderAfter == assetBalanceOfSenderBefore - assetsToDeposit, "Assert 2";
    assert assetBalanceOfCustodianAfter == assetBalanceOfCustodianBefore + assetsToDeposit, "Assert 3";
    assert assetBalanceOfOtherAfter == assetBalanceOfOtherBefore, "Assert 4";
    assert totalSharesAfter == totalSharesBefore + newShares, "Assert 5";
    assert sharesReceiverAfter == sharesReceiverBefore + newShares, "Assert 6";
    assert sharesOtherAfter == sharesOtherBefore, "Assert 7";
    assert totalSharesBefore > 0 =>
           totalAssetsAfter * 10^18 / totalSharesAfter >= totalAssetsBefore * 10^18 / totalSharesBefore, "Assert 8";
}

// Verify revert rules on deposit
rule deposit_revert(address asset, address receiver, uint256 assetsToDeposit) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    address pocket = pocket();

    mathint assetsToDepositValue = defGetAssetValue(asset, assetsToDeposit, false);
    mathint newShares = defConvertToShares(assetsToDepositValue);

    mathint totalShares = totalShares();

    mathint usdcBalanceOfPocket = usdc.balanceOf(pocket);
    mathint usdsBalanceOfPSM = usds.balanceOf(currentContract);
    mathint susdsBalanceOfPSM = susds.balanceOf(currentContract);

    mathint conversionRate = rateProvider.getConversionRate();

    mathint totalAssets = defGetUsdcValue(usdcBalanceOfPocket) +
                          defGetUsdsValue(usdsBalanceOfPSM) +
                          defGetSUsdsValue(susdsBalanceOfPSM, false);

    // Practical assumptions
    require asset.balanceOf(e, e.msg.sender) >= assetsToDeposit;
    require asset.allowance(e, e.msg.sender, currentContract) >= assetsToDeposit;
    require asset == susds || assetsToDeposit * 10^18 <= max_uint256;
    require asset != susds || assetsToDeposit * conversionRate <= max_uint256;
    require usdcBalanceOfPocket * 10^18 <= max_uint256;
    require usdsBalanceOfPSM * 10^18 <= max_uint256;
    require susdsBalanceOfPSM * conversionRate <= max_uint256;
    require totalAssets <= max_uint256;
    // ERC20 assumption
    require asset.totalSupply(e) >= asset.balanceOf(e, e.msg.sender) + asset.balanceOf(e, defGetAssetCustodian(asset));

    requireInvariant sharesSum_equals_totalShares;

    deposit@withrevert(e, asset, receiver, assetsToDeposit);

    bool revert1 = e.msg.value > 0;
    bool revert2 = assetsToDeposit == 0;
    bool revert3 = asset != usdc && asset != usds && asset != susds;
    bool revert4 = totalAssets > 0 && assetsToDepositValue * totalShares > max_uint256;
    bool revert5 = totalShares + newShares > max_uint256;

    assert lastReverted <=> revert1 || revert2 || revert3 ||
                            revert4 || revert5, "Revert rules failed";
}

// Verify correct storage changes for non reverting withdraw
rule withdraw(address asset, address receiver, uint256 maxAssetsToWithdraw) {
    env e;

    require currentContract._usdcPrecision  == 10^8  &&
            currentContract._usdsPrecision  == 10^18 &&
            currentContract._susdsPrecision == 10^18;

    address other;
    address custodian = defGetAssetCustodian(asset);
    require other != receiver && other != custodian;
    address other2;
    require other2 != e.msg.sender;

    mathint assetBalanceOfReceiverBefore = asset.balanceOf(e, receiver);
    mathint assetBalanceOfCustodianBefore = asset.balanceOf(e, custodian);
    mathint assetBalanceOfOtherBefore = asset.balanceOf(e, other);
    mathint totalSharesBefore = totalShares();
    mathint sharesSenderBefore = shares(e.msg.sender);
    mathint sharesOtherBefore = shares(other2);
    mathint assetsWithdrawnAux = assetBalanceOfCustodianBefore < maxAssetsToWithdraw ? assetBalanceOfCustodianBefore : maxAssetsToWithdraw;
    mathint sharesToBurnAux = defConvertToSharesRoundUp(defGetAssetValue(asset, assetsWithdrawnAux, true));
    mathint assetsWithdrawn = sharesToBurnAux > sharesSenderBefore ? defConvertToAssets(asset, sharesSenderBefore) : assetsWithdrawnAux;
    mathint sharesToBurn = sharesToBurnAux > sharesSenderBefore ? sharesSenderBefore : sharesToBurnAux;
    mathint totalAssetsBefore = totalAssets();

    // ERC20 assumption
    require asset.totalSupply(e) >= assetBalanceOfReceiverBefore + assetBalanceOfCustodianBefore + assetBalanceOfOtherBefore;

    requireInvariant sharesSum_equals_totalShares;

    mathint assetsWithdrawnRet = withdraw(e, asset, receiver, maxAssetsToWithdraw);

    mathint assetBalanceOfReceiverAfter = asset.balanceOf(e, receiver);
    mathint assetBalanceOfCustodianAfter = asset.balanceOf(e, custodian);
    mathint assetBalanceOfOtherAfter = asset.balanceOf(e, other);
    mathint totalSharesAfter = totalShares();
    mathint sharesSenderAfter = shares(e.msg.sender);
    mathint sharesOtherAfter = shares(other2);
    mathint totalAssetsAfter = totalAssets();

    assert assetsWithdrawnRet == assetsWithdrawn, "Assert 1";
    assert receiver != custodian => assetBalanceOfReceiverAfter == assetBalanceOfReceiverBefore + assetsWithdrawn, "Assert 2";
    assert receiver != custodian => assetBalanceOfCustodianAfter == assetBalanceOfCustodianBefore - assetsWithdrawn, "Assert 3";
    assert receiver == custodian => assetBalanceOfReceiverAfter == assetBalanceOfReceiverBefore, "Assert 4";
    assert assetBalanceOfOtherAfter == assetBalanceOfOtherBefore, "Assert 5";
    assert totalSharesAfter == totalSharesBefore - sharesToBurn, "Assert 6";
    assert sharesSenderAfter == sharesSenderBefore - sharesToBurn, "Assert 7";
    assert sharesOtherAfter == sharesOtherBefore, "Assert 8";
    assert totalSharesBefore > 0 && totalSharesAfter > 0 =>
           totalAssetsAfter * 10^18 / totalSharesAfter >= totalAssetsBefore * 10^18 / totalSharesBefore, "Assert 9";
    assert totalSharesBefore > 0 && totalSharesAfter == 0 =>
           sharesSenderBefore == totalSharesBefore, "Assert 10";
}

// Verify revert rules on withdraw
rule withdraw_revert(address asset, address receiver, uint256 maxAssetsToWithdraw) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    address pocket = pocket();

    mathint totalShares = totalShares();

    mathint usdcBalanceOfPocket = usdc.balanceOf(pocket);
    mathint usdsBalanceOfPSM = usds.balanceOf(currentContract);
    mathint susdsBalanceOfPSM = susds.balanceOf(currentContract);

    mathint conversionRate = rateProvider.getConversionRate();
    mathint sharesSender = shares(e.msg.sender);

    mathint totalAssets = defGetUsdcValue(usdcBalanceOfPocket) +
                          defGetUsdsValue(usdsBalanceOfPSM) +
                          defGetSUsdsValue(susdsBalanceOfPSM, false);

    address custodian = defGetAssetCustodian(asset);

    mathint assetBalanceOfCustodian = asset.balanceOf(e, custodian);

    mathint assetsWithdrawnAux = assetBalanceOfCustodian < maxAssetsToWithdraw ? assetBalanceOfCustodian : maxAssetsToWithdraw;
    mathint sharesToBurnAux = defConvertToSharesRoundUp(defGetAssetValue(asset, assetsWithdrawnAux, true));
    mathint assetsWithdrawn = sharesToBurnAux > sharesSender ? defConvertToAssets(asset, sharesSender) : assetsWithdrawnAux;
    mathint assetsWithdrawnAuxValue = defGetAssetValue(asset, assetsWithdrawnAux, true);

    // Practical assumptions
    require asset == susds || assetsWithdrawnAux * 10^18 <= max_uint256;
    require asset != susds || assetsWithdrawnAux * conversionRate <= max_uint256;
    require defTotalAssets() == 0 || assetsWithdrawnAuxValue * totalShares <= max_uint256;
    require sharesToBurnAux <= sharesSender ||
            asset == usdc  && sharesSender * currentContract._usdcPrecision <= max_uint256 ||
            asset == usds  && sharesSender * currentContract._usdsPrecision <= max_uint256 ||
            asset == susds && sharesSender * 10^9 * currentContract._susdsPrecision <= max_uint256;
    require usdcBalanceOfPocket * 10^18 <= max_uint256;
    require usdsBalanceOfPSM * 10^18 <= max_uint256;
    require susdsBalanceOfPSM * conversionRate <= max_uint256;
    require totalAssets <= max_uint256;
    // Setup assumption
    require custodian == currentContract || asset.allowance(e, custodian, currentContract) == max_uint256;
    // ERC20 assumption
    require asset.totalSupply(e) >= asset.balanceOf(e, custodian) + asset.balanceOf(e, receiver);

    requireInvariant sharesSum_equals_totalShares;

    withdraw@withrevert(e, asset, receiver, maxAssetsToWithdraw);

    bool revert1 = e.msg.value > 0;
    bool revert2 = maxAssetsToWithdraw == 0;
    bool revert3 = asset != usdc && asset != usds && asset != susds;

    assert lastReverted <=> revert1 || revert2 || revert3, "Revert rules failed";
}

// Verify correct behaviour for previewDeposit getter
rule previewDeposit(address asset, uint256 assetsToDeposit) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint newShares = defConvertToShares(defGetAssetValue(asset, assetsToDeposit, false));

    mathint newSharesRet = previewDeposit(e, asset, assetsToDeposit);

    assert newSharesRet == newShares, "Assert 1";
}

// Verify correct behaviour for previewDeposit getter
rule previewWithdraw(address asset, uint256 maxAssetsToWithdraw) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    address custodian = defGetAssetCustodian(asset);
    mathint assetBalanceOfCustodian = asset.balanceOf(e, custodian);
    mathint sharesSender = shares(e.msg.sender);
    mathint assetsWithdrawnAux = assetBalanceOfCustodian < maxAssetsToWithdraw ? assetBalanceOfCustodian : maxAssetsToWithdraw;
    mathint sharesToBurnAux = defConvertToSharesRoundUp(defGetAssetValue(asset, assetsWithdrawnAux, true));
    mathint assetsWithdrawn = sharesToBurnAux > sharesSender ? defConvertToAssets(asset, sharesSender) : assetsWithdrawnAux;
    mathint sharesToBurn = sharesToBurnAux > sharesSender ? sharesSender : sharesToBurnAux;

    mathint sharesToBurnRet; mathint assetsWithdrawnRet;
    sharesToBurnRet, assetsWithdrawnRet = previewWithdraw(e, asset, maxAssetsToWithdraw);

    assert sharesToBurnRet == sharesToBurn, "Assert 1";
    assert assetsWithdrawnRet == assetsWithdrawn, "Assert 2";
}

// Verify correct behaviour for previewSwapExactIn getter
rule previewSwapExactIn(address assetIn, address assetOut, uint256 amountIn) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint amountOut = defGetSwapQuote(assetIn, assetOut, amountIn, false);

    mathint amountOutRet = previewSwapExactIn(e, assetIn, assetOut, amountIn);

    assert amountOutRet == amountOut, "Assert 1";
}

// Verify correct behaviour for previewSwapExactOut getter
rule previewSwapExactOut(address assetIn, address assetOut, uint256 amountOut) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint amountIn = defGetSwapQuote(assetOut, assetIn, amountOut, true);

    mathint amountInRet = previewSwapExactOut(e, assetIn, assetOut, amountOut);

    assert amountInRet == amountIn, "Assert 1";
}

// Verify correct behaviour for convertToAssets getter
rule convertToAssets(address asset, uint256 numShares) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint assets = asset != susds || rateProvider.getConversionRate() > 0 ? defConvertToAssets(asset, numShares) : 0;

    mathint assetsRet = convertToAssets(asset, numShares);

    assert assetsRet == assets, "Assert 1";
}

// Verify correct behaviour for convertToAssetValue getter
rule convertToAssetValue(uint256 numShares) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint assetValue = defConvertToAssetValue(numShares);

    mathint assetValueRet = convertToAssetValue(numShares);

    assert assetValueRet == assetValue, "Assert 1";
}

// Verify correct behaviour for convertToShares getter
rule convertToShares(uint256 assetValue) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint shares = defConvertToShares(assetValue);

    mathint sharesRet = convertToShares(assetValue);

    assert sharesRet == shares, "Assert 1";
}

// Verify correct behaviour for convertToShares getter
rule convertToShares2(address asset, uint256 assets) {
    env e;

    require currentContract._usdcPrecision > 0 && currentContract._usdsPrecision > 0 && currentContract._susdsPrecision > 0;

    mathint shares = defConvertToShares(defGetAssetValue(asset, assets, false));

    mathint sharesRet = convertToShares(asset, assets);

    assert sharesRet == shares, "Assert 1";
}
