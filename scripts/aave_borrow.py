from brownie import config, interface, network  # type: ignore

from scripts.get_weth import get_account, get_weth
from scripts.helpful_scripts import get_account

amount = 10 ** 17


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved")
    return tx


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    toEth = 10 ** 18
    available_borrow_eth = available_borrow_eth / toEth
    total_collateral_eth = total_collateral_eth / toEth
    total_debt_eth = total_debt_eth / toEth
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    return float(dai_eth_price_feed.latestRoundData()[1] / 10 ** 18)


def replay_all(amount, lending_pool, account):
    approve_erc20(
        amount * 10 ** 18,
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    replay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    replay_tx.wait(1)
    print("Repaid borrowed asset!")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited")
    borrowable_eth, debt_eth = get_borrowable_data(lending_pool, account)
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"Borrowing {amount_dai_to_borrow} DAI")
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        amount_dai_to_borrow * 10 ** 18,
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    get_borrowable_data(lending_pool, account)
    print("Repaying borrowed asset...")
    replay_all(amount, lending_pool, account)
    get_borrowable_data(lending_pool, account)
