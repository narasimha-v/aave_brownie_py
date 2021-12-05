from brownie import config, interface, network  # type: ignore

from scripts.helpful_scripts import get_account


def get_weth():
    """
    Mints WETH by depositing ETH.
    """
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": 0.1 * 10 ** 18})
    tx.wait(1)
    print(f"Reieved 0.1 WETH")
    return tx


def main():
    get_weth()
