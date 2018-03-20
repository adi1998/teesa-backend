from flask import *
from web3.contract import ConciseContract
from flask_cors import CORS
from flask_sockets import Sockets

import json
import web3
import os
import hmac
import pickle
import datetime

app = Flask(__name__)

contract_address = "0xcebe6483903dfef7e954ae7954d6b07755b55d66"

abi = json.load(open("abi.json"))["abi"]
#CORS(app)
sockets =  Sockets(app)

@sockets.route("/live_txn")
def live_txn(ws):
	while not ws.closed:
		message = ws.receive()
		# TODO : process and send transactions

		print (message)

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', 'http://10.42.0.1:3000')
  response.headers.add('Access-Control-Allow-Credetials','true')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@app.route("/",methods=["POST"])
def home():
	try:
		db = json.load(open("db.json"))
	except Exception as e:
		print(e)
		db={}
	data = eval(list(request.form)[0])
	username = data.get("username",'')
	session = data.get("session","")
	print (request.form)
	print (request.cookies)
	if not (username and session):
		return jsonify(isloggedin=False)
	password = request.form.get("password")
	HMAC = hmac.new(b"secretsweg",bytes(username,"utf-8")).hexdigest()
	if HMAC!=session:
		resp = jsonify(isloggedin = False)
		resp.set_cookie("session","",expires=0)
		resp.set_cookie("username","",expires=0)
		return resp
	address = db[username]
	return jsonify(address = address, username = username,isloggedin=True)

@app.route("/create_account", methods=["POST"])
def create_account():
	w3 = web3.Web3(web3.HTTPProvider("http://localhost:8545"))
	try:
		db = json.load(open("db.json"))
	except Exception as e:
		print(e)
		db = {}
	try:
		transactionDB = pickle.load(open("transaction.json","rb"))
	except Exception as e:
		print(e)
		transactionDB={w3.eth.coinbase.lower():[]}
	data = eval(list(request.form)[0])
	
	username = data.get("username","")
	if username in db:
		return jsonify(success = False)
	password = data.get("password","")
	try:
		address = w3.personal.newAccount(password)
	except:
		return jsonify(success = 3)
	keys = [json.load(open("/home/aditya/.ethereum/keystore/"+i)) for i in os.listdir("/home/aditya/.ethereum/keystore")]
	db[username] = address
	json.dump(db,open("db.json","w"))
	for i in keys:
		if i["address"] == address[2:]:
			w3.personal.unlockAccount(w3.eth.coinbase,"starlord")
			w3.eth.sendTransaction({"from":w3.eth.coinbase,"to":address,"value":10**18})
			contractInstance = w3.eth.contract(abi,contract_address,ContractFactoryClass=ConciseContract)
			txnHash=contractInstance.transferTo(address,500,transact={"from":w3.eth.coinbase})
			if address not in transactionDB:
				transactionDB[address]=[]
			txnDate = (datetime.datetime.now()+datetime.timedelta(hours=5,minutes=30)).isoformat(" ").split(".")[0]
			transactionDB[w3.eth.coinbase.lower()].append((address,-500,txnDate,txnHash))
			transactionDB[address].append((w3.eth.coinbase.lower(),500,txnDate,txnHash))
			pickle.dump(transactionDB,open("transaction.json","wb"))
			return jsonify(success = True,address = address)
	return jsonify(success = False)

@app.route("/login",methods=["POST"])
def login():
	db = json.load(open("db.json"))
	w3 = web3.Web3(web3.HTTPProvider("http://localhost:8545"))
	data = eval(list(request.form)[0])
	username = data.get("username",None)
	print (request.form)
	print (username)
	if username not in db:
		return jsonify(success = False)

	password = data.get("password")
	print (password)
	address = db[username]
	if  not w3.personal.unlockAccount(address,password):
		return jsonify(success = False)
	cookie = hmac.new(bytes("secretsweg","utf-8"),bytes(username,"utf-8")).hexdigest()
	res = make_response(jsonify(success = True,cookie = cookie,username = username,address=address))
	return res

@app.route("/send_money", methods = ["POST"])
def send_money():
	try:
		db = json.load(open("db.json"))
	except Exception as e:
		print(e)
		db={}
	try:
		transactionDB = pickle.load(open("transaction.json","rb"))
	except Exception as e:
		print(e)
		transactionDB={}
	print (transactionDB)
	w3 = web3.Web3(web3.HTTPProvider("http://localhost:8545"))
	data = eval(list(request.form)[0])
	username = data.get("username","")
	session = data.get("session","")
	password = data.get("password","")
	HMAC = hmac.new(bytes("secretsweg","utf-8"),bytes(username,"utf-8")).hexdigest()
	if HMAC!=session:
		resp = jsonify(success = False)
		return resp
	address = db[username]
	to = data.get("to","")
	print(data.get("amount"))
	amount = int(data.get("amount",0))
	if  not w3.personal.unlockAccount(address,password):
		return jsonify(success = False)
	try:
		contractInstance = w3.eth.contract(abi,contract_address,ContractFactoryClass=ConciseContract)
		txnHash=contractInstance.transferTo(to,amount,transact={"from":address})
		if address not in transactionDB:
			transactionDB[address]=[]
		txnDate = (datetime.datetime.now()+datetime.timedelta(hours=5,minutes=30)).isoformat(" ").split(".")[0]
		transactionDB[address].append((to,-amount,txnDate,txnHash))
		if to not in transactionDB:
			transactionDB[to]=[]
		transactionDB[to].append((address,amount,txnDate,txnHash))
	except Exception as e:
		print(e)
		return  jsonify(success = False)
	else:
		print (transactionDB)
		pickle.dump(transactionDB,open("transaction.json","wb"))
		return jsonify(success = True)

@app.route("/get_all_transactions",methods=["POST"])
def get_all_transactions():
	data = eval(list(request.form)[0])
	transactionDB = pickle.load(open("transaction.json","rb"))
	print (transactionDB)
	for i in transactionDB:
		transactionDB[i]=transaction[i][::-1]
	try:
		return jsonify(transactionDB)
	except Exception as e:
		print (e)
		return jsonify(success = False)

@app.route("/get_transactions", methods = ["POST"])
def get_transactions():
	data = eval(list(request.form)[0])
	address = data.get("address")
	transactionDB = pickle.load(open("transaction.json","rb"))
	print (transactionDB)
	try:
		return jsonify(transactionDB[address][::-1])
	except Exception as e:
		print (e)
		return jsonify(success = False)

@app.route("/get_encrypted_key", methods = ["POST"])
def get_encrypted_key():
	address = request.form.get("address")[2:]
	keys = [json.load(open("/root/mychain/chaindata/keystore/"+i)) for i in os.listdir("/root/mychain/chaindata/keystore")]
	for i in keys:
		if i["address"] == address:
			return jsonify(i)
	return jsonify(success = False)
	

@app.route("/get_balance", methods = ["POST"])
def get_balance():
	w3 = web3.Web3(web3.HTTPProvider("http://localhost:8545"))
	address = eval(list(request.form)[0]).get("address","")
	print (request.form)
	try:
		contractInstance = w3.eth.contract(abi,contract_address,ContractFactoryClass=ConciseContract)
	except:
		return  jsonify(success = False)
	else:
		accBal = contractInstance.accountBalance(address)
		print(accBal)
		return jsonify(success = True,balance = accBal)

@app.route("/get_profile", methods = ["POST"])
def get_profile():
	pass

if __name__=="__main__":
	app.run(debug=True,port=8000,host='0.0.0.0')