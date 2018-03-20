import json
import web3

from web3 import Web3, HTTPProvider, TestRPCProvider
from solc import compile_source
from web3.contract import ConciseContract

# Solidity source code
contract_source_code = '''
pragma solidity ^0.4.17; 

contract TeesaCoin{

    address public creator;
    
    uint256 public totalTokens;

    mapping (address => uint256) public balanceOf;
    
    function Teesa(uint256 initialSupply){
        creator = msg.sender;
        totalTokens = initialSupply;
        balanceOf[creator] = initialSupply;
    }

    function transferTo(address to, uint256 value){
        require(balanceOf[msg.sender] >= value);
        require(balanceOf[to] + value >= balanceOf[to]);
        balanceOf[msg.sender] -= value;
        balanceOf[to] = value;
    }

    function accountBalance(address user) view public returns (uint256){
        return balanceOf[user];
    }

    // maintenance functions
    function getEther(address user) public{
        if (user == creator){
            user.transfer(this.balance);
        }
    }

    function kill() {
        if (creator == msg.sender){
            suicide(creator);
        }   
    }

    function() public payable { }
}
'''

compiled_sol = compile_source(contract_source_code) # Compiled source code
contract_interface = compiled_sol['<stdin>:TeesaCoin']

# web3.py instance
w3 = Web3(HTTPProvider("http://localhost:8545"))
#w3.personal.unlockAccount(w3.eth.coinbase,"1234")

# Instantiate and deploy contract
contract = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

# Get transaction hash from deployed contract
tx_hash = contract.deploy(transaction={'from': w3.eth.accounts[0], 'gas': 510000})

print(tx_hash)
#print(abi)

# Gets tx receipt to get contract address
tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
print(tx_hash)
contract_address = tx_receipt['contractAddress']
print(contract_address)
# Contract instance in concise mode
print(contract_interface["abi"])
contract_instance = w3.eth.contract(contract_interface['abi'], contract_address)
print (contract_instance.accountBalance(w3.eth.coinbase))
