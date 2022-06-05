from ast import arg
from datetime import date
import errno
from multiprocessing.connection import wait
import os
from pickle import TRUE
from queue import PriorityQueue
import random
import signal
import sys
import time
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from web3 import Web3
import json
import bs4
import re
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

INFURA_SECRET_KEY = ''  # https://infura.io/
ETHERSCAN_KEY = '' # https://etherscan.io/myapikey
TG_BOT_TOKEN = '' # telegram  @BotFather
TG_USER_ID = ''  # telegram @getmyid_bot
MY_ADDERESS = '0x123123' # 你的eth地址
MY_PRIVATE_KEY = '0x123ddd' # eth私钥 

MAX_GAS_FEE = 50  #最大汽油费
MAX_MINT_PER_NFT = 5   #每个nft的最大可mint数量，超过就不mint了（不精准，通过单个hash获取，非abi调用）

FOLLOW_ADDR_LIST = ['0xe749e9E7EAa02203c925A036226AF80e2c79403E','0x4c86f3d2e3d4c0a7cc99a2c45fcaaa1b10d313b6'] #跟单mint地址，找获利高的
MAX_ETH_FOR_FOLLOW = 0.01  #跟单时能接受的最大mint价格

blacklist = ['Ape','Bear','bear','Duck','duck','Pixel','pixel','Not','Okay','Woman','Baby','baby','Goblin','goblin','Ai','AI'] #黑名单，要求精准 所以区分大小写

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",
    'Accept': 'text/html',
    'Accept-Language': 'en-US,en;q=0.5',
}

def print_green(message):
    print(f'\033[1;32m{message}\033[0m')

def print_red(message):
    print(f'\033[1;31m{message}\033[0m')

def print_blue(message):
    print(f'\033[1;34m{message}\033[0m')

def TG_send_message(message):
    url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage'
    params = {
        'chat_id': TG_USER_ID,
        'text': message
    }
    try:
        requests.post(url, params)
    except Exception as e:
        print_red(f"[TG_send_message] error: {e} ")

def get_w3_by_network():
    infura_url = f'https://mainnet.infura.io/v3/{INFURA_SECRET_KEY}' 
    w3 = Web3(Web3.HTTPProvider(infura_url))
    return w3

def get_random_float(min,max):
    return round(random.uniform(min, max), 2)

def get_random_int(min,max):
    return random.randint(min, max)

def get_gasprice():
    try:
        url = 'https://api.debank.com/chain/gas_price_dict_v2?chain=eth'
        r = requests.get(url, headers=headers,verify=False)
        if r.status_code == 200:
            data = json.loads(r.text)
            fast = int(data['data']['fast']['price']) / 1000000000
            if fast > MAX_GAS_FEE:
                print_red(f'[get_gasprice] gasprice too high !!  >{fast}')
                return 0
            else:
                return get_random_float(fast - 3, fast + 3)
    except Exception as e:
        print_red(f"[get_gasprice] error: {e}")
        return 0

def get_info_by_hash(hash):
    try:
        url = f'https://etherscan.io/tx/{hash}'
        r = requests.get(url, headers=headers,verify=False)
        if r.status_code == 200:
            soup = bs4.BeautifulSoup(r.text, 'html.parser')
            text = soup.find('div', id='ContentPlaceHolder1_maintable')
            mint_count = re.findall(r"Tokens Transferred: \(.*? ERC-", text.text)
            if mint_count:
                mint_count = int(re.findall(r"\d+", mint_count[0])[0])
            else:
                mint_count = 1
                # print_red(f"[get_info_by_hash] error: mint_count not found , hash: {hash}")
                # return {"status":False}
            if 'Mint of' in text.text:
                function_name = re.findall(r"Function: (.*?)\(", text.text)
                if function_name:
                    function_name = function_name[0]
                    nft_name = soup.find('span', class_='hash-tag text-truncate mr-1')["title"]
                    return {"status":True, "mint_count":mint_count, "function_name":function_name, "nft_name":nft_name}
                else:
                    print_red(f"[get_info_by_hash] error: function_name not found , probably not open source , hash: {hash}")
                    return {"status":False,'error':'function_name not found'}
            else:
                return {"status":False,'error':'not mint','hash':hash}
        else:
            print_red(f'[get_info_by_hash] status_code error: {r.status_code}')
            return {"status":False,'error':'status_code error'}
    except Exception as e:
        print_red(f"[get_info_by_hash] error: {e}")
        return {"status":False,'error':e}

def get_contract_abi(contract_address):
    try:
        url = f'https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={ETHERSCAN_KEY}'
        r = requests.get(url, headers=headers,verify=False)
        if r.status_code == 200:
            data = json.loads(r.text)
            if data['status'] == "1":
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        print_red(f"[get_contract_abi] error: {e} ")
        return False

def cancel_mint(w3, chainId):
    print_green('[cancel_mint] start')
    from_address = Web3.toChecksumAddress(MY_ADDERESS)
    nonce = w3.eth.getTransactionCount(from_address) 
    gas_fee = get_gasprice()
    if gas_fee == 0:
        return {'status': 'failed', 'error': 'get gas price error', 'task': 'cancel_mint'}
    priorityfee = 2
    params = {
        'from': from_address,
        'nonce': nonce,
        'to': from_address,
        'value': w3.toWei(0, 'ether'),
        'gas': 21000,
        'maxFeePerGas': w3.toWei(gas_fee, 'gwei'),
        'maxPriorityFeePerGas': w3.toWei(priorityfee, 'gwei'),
        'chainId': chainId,
    }
    try:
        signed_tx = w3.eth.account.signTransaction(params, private_key=MY_PRIVATE_KEY)
        txn = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return {'status': 'succeed', 'txn_hash': w3.toHex(txn), 'task': 'cancel_mint'}
    except Exception as e:
        return {'status': 'failed', 'error': e, 'task': 'cancel_mint'}

def do_mint(w3, chainId, contract_address,input_data,gas,amount):
    print_green('[do_mint] start')
    from_address = Web3.toChecksumAddress(MY_ADDERESS)
    contract_address = Web3.toChecksumAddress(contract_address)
    nonce = w3.eth.getTransactionCount(from_address)
    gas_fee = get_gasprice()
    if gas_fee == 0:
        return {'status': 'failed', 'error': 'get gas price error', 'task': 'do_mint'}
    priorityfee = get_random_float(1,2)
    gas = get_random_int(gas,gas+50000)
    print_green(f'[do_mint] gas: {gas}  {gas_fee}  {priorityfee}')
    params = {
        'from': from_address,
        'nonce': nonce,
        'to': contract_address,
        'value': w3.toWei(amount, 'ether'),
        'gas': gas,
        'maxFeePerGas': w3.toWei(gas_fee, 'gwei'),
        'maxPriorityFeePerGas': w3.toWei(priorityfee, 'gwei'),
        'chainId': chainId,
        'data': input_data,
    }
    try:
        signed_tx = w3.eth.account.signTransaction(params, private_key=MY_PRIVATE_KEY)
        txn = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return {'status': 'succeed', 'txn_hash': w3.toHex(txn), 'task': 'do_mint'}
    except Exception as e:
        return {'status': 'failed', 'error': e, 'task': 'do_mint'}

last_token_addr = ''
def get_free_mint_info():
    global last_token_addr
    url = 'https://www.acnft.xyz/api/nft/freeMintAlert?type=0'
    try:
        response = requests.get(url,headers=headers, verify=False)
        if response.status_code == 200:
            if response.json()['message'] == 'Api请求成功':
                tokens = response.json()['data']['list'][0]
                token_address = tokens['token_address']
                if last_token_addr == '':
                    last_token_addr = token_address
                    print_green(f'[get_free_mint_info] init success')
                    return {'status': 'init', 'task': 'get_free_mint_info'}
                if token_address == last_token_addr:
                    return {'status': 'failed', 'error': 'token_address not update', 'task': 'get_free_mint_info'}
                else:
                    last_token_addr = token_address
                    nft_name = tokens['nft_name']
                    os_link = tokens['os_link']
                    api = f'https://api.etherscan.io/api?module=account&action=txlist&address={token_address}&startblock=0&endblock=99999999&page=1&offset=50&sort=desc&apikey={ETHERSCAN_KEY}'
                    r = requests.get(api,verify=False)
                    if r.status_code == 200 and r.json()['message'] == 'OK':
                        result_count = len(r.json()['result'])
                        if result_count < 5:
                            return {'status': 'failed', 'error': 'mint count less than 5', 'task': 'get_free_mint_info'}
                        else:
                            FIND = 0
                            for i in range(result_count):
                                last_result = r.json()['result'][i]
                                isError = last_result['isError']
                                if int(isError) == 1:
                                    continue
                                eth_value = last_result['value']
                                if int(eth_value) > 0:
                                    continue
                                to_address = last_result['to']
                                if to_address.lower() != token_address.lower():
                                    continue
                                from_address = last_result['from'] 
                                from_address = from_address[2:]
                                input_data = last_result['input']
                                if from_address in input_data:
                                    my_adderss = MY_ADDERESS[2:].lower()
                                    input_data = input_data.replace(from_address, my_adderss)
                                hash = last_result['hash']
                                FIND = 1
                                break
                            if FIND == 1:
                                return {'status': 'succeed', 'type':'free','token_address': token_address, 'nft_name': nft_name, 'os_link': os_link, 'hash': hash, 'input_data': input_data, 'value': '0', 'gas': last_result['gas'], 'task': 'get_free_mint_info'}
                            else:
                                return {'status': 'failed', 'error': 'mint not found', 'task': 'get_free_mint_info'}
                    else:
                        print_red(f'[get_free_mint_info] get api error, status_code:{r.status_code}')
                        return {'status': 'failed', 'error': 'get api error', 'task': 'get_free_mint_info'}
                    
            else:
                print_red('[get_free_mint_info] error , message: {}'.format(response.json()['message']))
                return {'status': 'failed', 'error': 'message: ' + response.json()['message'], 'task': 'get_free_mint_info'}
        return {'status': 'failed', 'error': 'status_code: ' + str(response.status_code), 'task': 'get_free_mint_info'}
    except Exception as e:
        print_red(f'[get_free_mint_info] error: {e}')
        return {'status': 'failed', 'error': e, 'task': 'get_free_mint_info'}

last_follow_txn = []
def get_follow_mint_info():
    global last_follow_txn
    for addr in FOLLOW_ADDR_LIST:
        time.sleep(1)
        if addr.lower() == MY_ADDERESS.lower():
            continue
        try:
            addr = addr.lower()
            url = f'https://api.etherscan.io/api?module=account&action=txlist&address={addr}&startblock=0&endblock=99999999&page=1&offset=10&sort=desc&apikey={ETHERSCAN_KEY}'
            r = requests.get(url,verify=False)
            if r.status_code == 200:
                if r.json()['status'] == '1':
                    hash_info = r.json()['result'][0]
                    if len(last_follow_txn) == 0:
                        for i in FOLLOW_ADDR_LIST:
                            last_follow_txn.append({'addr': i.lower(), 'hash':''})
                    for i in last_follow_txn:
                        if i['addr'] == addr:
                            if len(i['hash']) == 0:
                                i['hash'] = hash_info['hash']
                                print_green(f'[get_follow_mint_info] follow addr {addr} init success')
                                break
                            else:
                                if i['hash'] == hash_info['hash']:
                                    break
                                else:
                                    i['hash'] = hash_info['hash']
                                    if hash_info['from'] != addr:
                                        break
                                    if hash_info['isError'] == '1':
                                        break
                                    # last_follow_txn = hash_info['hash']
                                    input_data = hash_info['input']
                                    addr = addr[2:]
                                    if addr in input_data:
                                        my_adderss = MY_ADDERESS[2:].lower()
                                        input_data = input_data.replace(addr, my_adderss)
                                    return {'status': 'succeed', 'type':'follow','token_address': hash_info['to'],'hash':hash_info['hash'],'input_data':input_data,'value':hash_info['value'],'gas':hash_info['gas'] , 'os_link': 'https://opensea.io/assets/' + hash_info['to'] + '/1', 'task': 'get_follow_mint_info'}
                    
                else:
                    print_red('[get_follow_mint_info] error , message: {}'.format(r.json()['message']))
                    continue
            else:
                print_red(f'[get_follow_mint_info] get api error, status_code:{r.status_code}')
                continue
        except Exception as e:
            print_red(f'[get_follow_mint_info] error: {e} , addr = {addr}')
            continue

    return {'status': 'failed'}



def loop_status(txn_hash):
    try:
        time.sleep(10)
        n = 0
        while True:
            n += 1
            if n > 60:
                return {'status': 'unknown', 'error': 'timeout 5 min', 'task': 'loop_status'}
            url = f"https://etherscan.io/txsHandler.ashx?strSearchVal={txn_hash}&toggleAction=popover&actionParam=txs"
            response = requests.get(url,headers=headers, verify=False)
            if response.status_code == 200:
                if 'Success' in response.text:
                    return {'status': 'succeed', 'task': 'loop_status'}
                elif 'Fail' in response.text:
                    return {'status': 'failed', 'task': 'loop_status'}
                elif 'Pending' not in response.text:
                    return {'status': 'unknown', 'task': 'loop_status'}
            else:
                return {'status': 'unknown', 'error': 'status_code = ' + str(response.status_code), 'task': 'loop_status'}
            time.sleep(5)
    except Exception as e:
        return {'status': 'unknown', 'error': e, 'task': 'loop_status'}

def save_file(status, txn_hash, nft_name, os_link):
    date_str = time.strftime("%Y-%m-%d", time.localtime())
    file = open(f'mint_task_{date_str}.txt', 'a+')
    file.write(f'status: {status}, nft_name: {nft_name}, eth_scan: https://etherscan.io/tx/{txn_hash},  os_link: {os_link}\n')
    file.close()

def name_in_file(nft_name):
    file_list = os.listdir(os.getcwd())
    for file in file_list:
        if 'mint_task_' in file:
            with open(file, 'r') as f:
                for line in f.readlines():
                    if nft_name in line:
                        return True
    return False


times = 0
minted_addr = []

def main(free_mint,follow_mint):
    global times
    global minted_addr
    try:
        while True:
            try:
                if free_mint == True:
                    nft_res = get_free_mint_info()
                    if nft_res['status'] == 'succeed':
                        break
                if follow_mint == True:
                    nft_res = get_follow_mint_info()
                    if nft_res['status'] == 'succeed':
                        break
                time.sleep(5)
            except Exception as e:
                print_red(f'[get nft_res] {e}')
        times += 1

        print_green(f'\n\n[main] trying to get info ...')
        target_address = nft_res['token_address']
        os_link = nft_res['os_link']
        hash_info = get_info_by_hash(nft_res['hash'])
        if hash_info['status'] == True:
            function_name = hash_info['function_name']
            nft_name = hash_info['nft_name']
        elif 'not mint' in hash_info['error']:
            print_red(f'[main] not mint , hash: {hash_info["hash"]}')
            return
        else:
            print_red(f'[main] get_info_by_hash error')
            return
        print_green(f'[main] found new nft: {nft_name}, NO {times} to mint , type: {nft_res["type"]}')
        print_green(f'[main] token_address: {target_address}')
        print_green(f'[main] os_link: {os_link}')
        gas_need = int(nft_res['gas'])
        input_data = nft_res['input_data']
        if nft_res['type'] == 'free':
            amount = 0
        else:
            amount = int(nft_res['value'])
            if amount != 0:
                amount = amount / 10 ** 18
                if amount > MAX_ETH_FOR_FOLLOW:
                    print_red(f'[main] amount: {amount} > MAX_ETH_FOR_FOLLOW , skip !!')
                    return
        print_green(f'[main] mint function: {function_name} , amount: {amount} , input: {input_data}')

        mint_count = int(hash_info['mint_count'])
        if mint_count > MAX_MINT_PER_NFT:
            print_red(f'[main] mint_count: {mint_count} > MAX_MINT_PER_NFT , skip !! hash: {nft_res["hash"]}')
            return


        if target_address not in minted_addr:
            minted_addr.append(target_address)
        else:
            print_red(f'[main] already minted, skip')
            return
        #blacklist check
        for word in blacklist:
            if word in nft_name:
                print_red(f'[main] nft_name : {nft_name} , blacklist : {word} , skip !!')
                return
        #minted check
        if name_in_file(nft_name):
            print_red(f'[main] {nft_name} already minted in file , skip !!')
            return
        #open source check
        if get_contract_abi(target_address) == False:
            print_red(f'[main] get_contract_abi failed, probably not open source, skip !!')
            return
        #mint function name check
        fuzz=['wl','admin','dev','og','white','list','owner']
        for f in fuzz:
            if f in function_name.lower():
                print_red(f"[main] mint_name: {function_name} , fuzz: {f} in function_name, skip !!")
                return
        start_time = time.time()
        w3 = get_w3_by_network()
        chainId = 1 # mainnet
        balance = w3.eth.get_balance(MY_ADDERESS) / 1e18
        print_blue(f'[balance] {balance}')
        if balance < amount:
            print_red('[balance] not enough')
            return

        result = do_mint(w3,chainId,target_address,input_data,gas_need,amount)
        if result['status'] == 'failed':
            print_red(f'[do_mint] result : {result}')
            if 'replacement transaction underpriced' in str(result['error']):
                res = cancel_mint(w3, chainId)
                if res['status'] == 'succeed':
                    print_red(f'[cancel_mint] {res["txn_hash"]} , sleep 1 min')
                    time.sleep(60)
                else:
                    print_red(f'[cancel_mint] {str(res["error"])}')
                    time.sleep(60)
            elif 'get gas price error' not in str(result['error']):
                print_red(f'[mint] unknown error , sleep 60s to try again')
                time.sleep(60)
            else:
                save_file('failed', 'gas_error', nft_name, os_link)
                print_red(f'[mint] {str(result["error"])}')
                return
            result = do_mint(w3,chainId,target_address,input_data,gas_need,amount)


        try:
            if result['status'] == 'succeed':
                end_time = time.time()
                txn_hash = result['txn_hash']
                print_blue(f'[mint] mint resquest succeed, txn_hash: {txn_hash} ')
                print_blue(f'[mint] took {round(end_time - start_time)} seconds , loop 5 minutes to confirm')
                receipt = loop_status(txn_hash)
                if receipt['status'] == 'succeed':
                    print_green(f'[mint] succeed , tx : https://etherscan.io/tx/{txn_hash}')
                elif receipt['status'] == 'failed':
                    print_red(f'[mint] failed , tx : https://etherscan.io/tx/{txn_hash}')
                elif receipt['status'] == 'unknown':
                    print_red(f'[mint] unknown , tx : https://etherscan.io/tx/{txn_hash}')

                TG_send_message(f"NO : {times}\n\ntype : {nft_res['type']}\n\nnft name : {nft_name}\n\nstatus : {receipt['status']}\n\nhash : https://etherscan.io/tx/{txn_hash}\n\nopensea : {os_link}")
                save_file(receipt['status'], txn_hash, nft_name, os_link)
            else:
                print_red(f'[mint] get mint result failed , {result}')
        except Exception as e:
            print_red(f"[loop status error] {e}")
    except Exception as e:
        print_red(f"[main error] {e}")


signal_handler = lambda signum, frame: print_green('\n\n[signal_handler] received signal , exit') or sys.exit(0)

if __name__ == "__main__":
    print_green('[main] start')
    signal.signal(signal.SIGINT, signal_handler)
    free_mint = False
    follow_mint = False
    input_1 = input('\033[1;36menable free mint? (y/n) >>>\033[0m ')
    if input_1.lower() == 'y':
        free_mint = True
    input_2 = input('\033[1;36menable follow mint? (y/n) >>>\033[0m ')
    if input_2.lower() == 'y':
        follow_mint = True
    if free_mint == False and follow_mint == False:
        print_red('[main] no mint mode , exit')
        sys.exit(0)
    while True:
        main(free_mint,follow_mint)
        print_blue(f'[main] time : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
        time.sleep(1)
