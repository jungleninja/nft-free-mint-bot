from ast import arg
from datetime import date
from multiprocessing.connection import wait
import os
from pickle import TRUE
from queue import PriorityQueue
import random
import time
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from web3 import Web3
import json
import bs4
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


INFURA_SECRET_KEY = ''  # https://infura.io/
ETHERSCAN_KEY = '' # https://etherscan.io/myapikey
TG_BOT_TOKEN = '' # telegram  @BotFather
TG_USER_ID = ''  # telegram @getmyid_bot
MY_ADDERESS = '' # your eth address
MY_PRIVATE_KEY = '' # your private key 

MAX_GAS_FEE = 50

blacklist = ['Ape','Bear','bear','Duck','duck','Pixel','pixel','Not','Okay','Woman','Baby','baby','Goblin','goblin','Ai']

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
        #{"_seconds":0.0007479190826416016,"data":{"fast":{"estimated_seconds":0,"front_tx_count":0,"price":68000000000.0},"normal":{"estimated_seconds":0,"front_tx_count":0,"price":49000000000.0},"slow":{"estimated_seconds":0,"front_tx_count":0,"price":33000000000.0}},"error_code":0}
        r = requests.get(url, headers=headers,verify=False)
        if r.status_code == 200:
            data = json.loads(r.text)
            fast = int(data['data']['fast']['price']) / 1000000000
            if fast > MAX_GAS_FEE:
                print_red(f'[get_gasprice] gasprice is too high !! {fast}')
                return 0
            else:
                return get_random_float(fast - 3, fast + 3)
    except Exception as e:
        print_red(f"[get_gasprice] error: {e}")
        return 0
    # try:
    #     url = f'https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_KEY}'
    #     r = requests.get(url,verify=False)
    #     # {"status":"1","message":"OK","result":{"LastBlock":"14839616","SafeGasPrice":"25","ProposeGasPrice":"25","FastGasPrice":"26","suggestBaseFee":"24.108529894","gasUsedRatio":"0.999680832120495,0.999610718387235,0.999998566659882,0.894152958626572,0.1707775"}}
    #     if r.status_code == 200 and r.json()['message'] == 'OK':
    #         SafeGasPrice = float(r.json()['result']['SafeGasPrice'])
    #         FastGasPrice = float(r.json()['result']['FastGasPrice'])
    #         if SafeGasPrice > 50:
    #             print_red(f'[get_gasprice] gasprice is too high !! {SafeGasPrice}')
    #             return 0
    #         return get_random_float(SafeGasPrice, FastGasPrice)
    #     else:
    #         print_red(f'[get_gasprice] status_code error: {r.status_code} or message error: {r.json()["message"]}')
    #         return 0
    # except Exception as e:
    #     print_red(f"[get_gasprice] error: {e}")
    #     return 0


def is_mint_func(hash):
    try:
        url = f'https://etherscan.io/tx/{hash}'
        r = requests.get(url, headers=headers,verify=False)
        #<div id="ContentPlaceHolder1_maintable" class="card-body py-4">
        if r.status_code == 200:
            soup = bs4.BeautifulSoup(r.text, 'html.parser')
            text = soup.find('div', id='ContentPlaceHolder1_maintable')
            if 'Mint of' in text.text:
                return True
            else:
                return False
            
            # soup = bs4.BeautifulSoup(r.text, 'lxml')
            # text = soup.find('textarea', {'id': 'inputdata'}).text
            # if text.lower().find('mint') > -1:
            #     return True
            # else:
            #     return False
        else:
            return False
    except Exception as e:
        print_red(f"[is_mint_func] error: {e}")
        return False

def cancel_mint(w3, chainId):
    print_green('[cancel_mint] start')
    from_address = Web3.toChecksumAddress(MY_ADDERESS)
    contract_address = Web3.toChecksumAddress(MY_ADDERESS)
    nonce = w3.eth.getTransactionCount(from_address) 
    gas_fee = get_gasprice()
    if gas_fee == 0:
        return {'status': 'failed', 'error': 'get gas price error', 'task': 'cancel_mint'}
    priorityfee = 2
    params = {
        'from': from_address,
        'nonce': nonce,
        'to': contract_address,
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



def mint_by_hash(w3,contract_address,amount,chainId):
    try:

        FIND = 0
        for page in range(1,6):
            if FIND == 1:
                break
            url = f'https://api.etherscan.io/api?module=account&action=txlist&address={contract_address}&startblock=0&endblock=99999999&page={page}&offset=50&sort=desc&apikey={ETHERSCAN_KEY}'
            r = requests.get(url,verify=False)

            if r.status_code == 200 and r.json()['message'] == 'OK':
                result_count = len(r.json()['result'])
                for i in range(result_count):
                    last_result = r.json()['result'][i]
                    isError = last_result['isError']
                    if isError == "1":
                        continue
                    eth_value = last_result['value']
                    if eth_value != "0":
                        continue
                    to_address = last_result['to']
                    if to_address != contract_address.lower():
                        continue
                    from_address = last_result['from'] 
                    #去除 0x
                    from_address = from_address[2:]
                    input_data = last_result['input']
                    if from_address in input_data:
                        my_adderss = MY_ADDERESS[2:]
                        input_data = input_data.replace(from_address, my_adderss)
                    tmp_input_data = input_data[:-2] 
                    if '0xa0712d6800000000000000000000000000000000000000000000000000000000000000' == tmp_input_data:
                        tmp_input_data = input_data[-2:]
                        tmp_input_data = int(tmp_input_data, 16)
                        if tmp_input_data > 3:
                            input_data = '0xa0712d680000000000000000000000000000000000000000000000000000000000000003'
                    hash = last_result['hash']
                    if is_mint_func(hash):
                        FIND = 1
                        break
        
        if FIND == 0:
            return {'status': 'failed', 'error': 'not find mint_hash', 'task': 'finding mint_hash'}
        
        print_blue(f'[input_data] {input_data}')

        from_address = Web3.toChecksumAddress(MY_ADDERESS)
        contract_address = Web3.toChecksumAddress(contract_address)
        nonce = w3.eth.getTransactionCount(from_address) 
        gas_fee = get_gasprice()
        if gas_fee == 0:
            return {'status': 'failed', 'error': 'gas price error', 'task': 'get gas price'}
        priorityfee = get_random_float(1,1.5)
        print_blue(f'[gas_price] {gas_fee} , {priorityfee}')
        params = {
            'from': from_address,
            'nonce': nonce,
            'to': contract_address,
            'value': w3.toWei(amount, 'ether'),
            'gas': get_random_int(210000, 250000),
            'maxFeePerGas': w3.toWei(gas_fee, 'gwei'),
            'maxPriorityFeePerGas': w3.toWei(priorityfee, 'gwei'),
            'chainId': chainId,
            'data': input_data,
        }
        try:
            signed_tx = w3.eth.account.signTransaction(params, private_key=MY_PRIVATE_KEY)
            txn = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            return {'status': 'succeed', 'txn_hash': w3.toHex(txn), 'task': 'mint_nft'}
        except Exception as e:
            return {'status': 'failed', 'error': e, 'task': 'mint_nft'}
    except Exception as e:
        return {'status': 'failed', 'error': e, 'task': 'mint_by_hash'}


# def mint_by_abi(w3,contract_address,amount,chainId):

#     try:
#         from_address = Web3.toChecksumAddress(MY_ADDERESS)
#         contract_address = Web3.toChecksumAddress(contract_address)
#         nonce = w3.eth.getTransactionCount(from_address) 

#         try:
#             response = requests.get(f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={ETHERSCAN_KEY}")
#         except Exception as e:
#             return {'status': 'failed', 'error': e, 'task': '[fetching ABI]'}
#         abi = response.json()['result']
#         print_blue(f'[fetch ABI] fetched successfully ,  {contract_address}')
#         contract = w3.eth.contract(address=contract_address, abi=abi)

#         # json 解析abi
#         try:
#             func = ''
#             contract_abi = json.loads(abi)
#             for function in contract_abi:
#                 if function['type'] == 'function':
#                     if 'mint' == function['name'] and 'uint256' == function['inputs'][0]['type']:
#                         func = function['name']
#                         mint = contract.functions.mint(1)
#                         break
#                     if 'Mint' == function['name'] and 'uint256' == function['inputs'][0]['type']:
#                         func = function['name']
#                         mint = contract.functions.Mint(1)
#                         break
#                     if 'freemint' == function['name'] and 'uint256' == function['inputs'][0]['type']:
#                         func = function['name']
#                         mint = contract.functions.freemint(1)
#                         break
#                     if 'freeMint' == function['name'] and len(function['inputs']) == 0:
#                         func = function['name']
#                         mint = contract.functions.freeMint()
#                         break
#                     if 'FreeMint' == function['name'] and 'uint256' == function['inputs'][0]['type']:
#                         func = function['name']
#                         mint = contract.functions.FreeMint(1)
#                         break
#                     if 'mintForAddress' == function['name'] and 'address' == function['inputs'][1]['type']:
#                         func = function['name']
#                         mint = contract.functions.mintForAddress(1,from_address)
#                         break
#                     if 'mintToAddress' == function['name'] and 'address' == function['inputs'][1]['type']:
#                         func = function['name']
#                         mint = contract.functions.mintToAddress(1,from_address)
#                         break
#                     if 'mintNft' == function['name'] and 'uint256' == function['inputs'][0]['type']:
#                         func = function['name']
#                         mint = contract.functions.mintNft(1)
#                         break
#                     if 'mintReserve' == function['name'] and 'address' == function['inputs'][1]['type']:
#                         func = function['name']
#                         mint = contract.functions.mintReserve(1,from_address)
#                         break
#         except Exception as e:
#             return {'status': 'failed', 'error': e, 'task': '[parse ABI]'}
#         if func == '':
#             return {'status': 'failed', 'error': 'not find mint func', 'task': '[find mint func]'}
#         print_blue(f'[function] {func}')

#         gas_fee = get_gasprice()
#         if gas_fee == 0:
#             return {'status': 'failed', 'error': 'gas price error', 'task': '[get gas price]'}
#         priorityfee = get_random_float(1,1.5)
#         print_blue(f'[gas price] {gas_fee} , {priorityfee}')

#         params = {
#             'from': from_address,
#             'nonce': nonce,
#             'value': w3.toWei(amount, 'ether'),
#             'gas': get_random_int(210000, 250000),
#             'maxFeePerGas': w3.toWei(gas_fee, 'gwei'),
#             'maxPriorityFeePerGas': w3.toWei(priorityfee, 'gwei'),
#             'chainId': chainId,
#         }
        
#         try:
#             tx = mint.buildTransaction(params)
#             signed_tx = w3.eth.account.signTransaction(tx, private_key=MY_PRIVATE_KEY)
#             txn = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
#             return {'status': 'succeed', 'txn_hash': w3.toHex(txn), 'task': 'mint_nft'}
#         except Exception as e:
#             return {'status': 'failed', 'error': e, 'task': 'mint_nft'}
#     except Exception as e:
#         return {'status': 'failed', 'error': e, 'task': 'eth_mint_nft'}

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

last_token_addr = ''

def loop_acnft():
    global last_token_addr
    url = 'https://www.acnft.xyz/api/nft/freeMintAlert?type=0'
    while True:
        try:
            response = requests.get(url,headers=headers, verify=False)
            if response.status_code == 200:
                if response.json()['message'] == 'Api请求成功':
                    tokens = response.json()['data']['list'][0]
                    token_address = tokens['token_address']
                    if last_token_addr == '':
                        last_token_addr = token_address
                        print_blue(f'[loop_acnft] init success')
                    if token_address == last_token_addr:
                        time.sleep(10)
                        continue
                    else:
                        last_token_addr = token_address
                        nft_name = tokens['nft_name']
                        token_img_ico_url = tokens['token_img_ico_url']
                        os_link = tokens['os_link']
                        return {'status': 'succeed', 'token_address': token_address, 'nft_name': nft_name, 'token_img_ico_url': token_img_ico_url, 'os_link': os_link, 'task': 'loop_acnft'}
                else:
                    print_red('[loop_acnft] error , message: {}'.format(response.json()['message']))
                    time.sleep(10)
                    continue

        except Exception as e:
            print_red(f'[loop_acnft] error: {e}')
            time.sleep(10)
            continue

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

def main():
    global times
    try:
        acnft_res = loop_acnft()
        if acnft_res['status'] == 'succeed':
            target_address = acnft_res['token_address']
            nft_name = acnft_res['nft_name']
            # token_img_ico_url = acnft_res['token_img_ico_url']
            os_link = acnft_res['os_link']
            times += 1
            print_green(f'\n\n[main] found new token: {nft_name}, NO {times} to mint')
            print_green(f'[main] token_address: {target_address}')
            print_green(f'[main] os_link: {os_link}')

        if target_address not in minted_addr:
            minted_addr.append(target_address)
        else:
            print_red(f'[main] already minted, skip')
            return
        
        for word in blacklist:
            if word in nft_name:
                print_red(f'[main] blacklist : {word} , skip !!')
                return
        
        if name_in_file(nft_name):
            print_red(f'[main] {nft_name} already minted in file , skip !!')
            return
            
        start_time = time.time()
        w3 = get_w3_by_network()
        amount = 0
        chainId = 1 # mainnet

        balance = w3.eth.get_balance(MY_ADDERESS) / 1e18
        print_blue(f'[balance] {balance}')
        if balance < 0.003:
            print_red('[balance] not enough')
            exit(1)

        print_blue('[mint] trying mint_by_hash')
        result = mint_by_hash(w3,target_address,amount,chainId)
        if result['status'] == 'failed':
            print_red(f'[mint_by_hash] result : {result}')
            if 'replacement transaction underpriced' in str(result['error']):
                res = cancel_mint(w3, chainId)
                if res['status'] == 'succeed':
                    print_red(f'[cancel_mint] {res["txn_hash"]} , sleep 1 min')
                    time.sleep(60)
                else:
                    print_red(f'[cancel_mint] {str(res["error"])}')
                    time.sleep(60)
            
            print_red(f'[mint] sleep 20s to try again')
            time.sleep(20)
            result = mint_by_hash(w3,target_address,amount,chainId)

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

                TG_send_message(f"NO : {times}\n\nnft name : {nft_name}\n\nstatus : {receipt['status']}\n\nhash : https://etherscan.io/tx/{txn_hash}\n\nopensea : {os_link}")
                save_file(receipt['status'], txn_hash, nft_name, os_link)
            else:
                print_red(f'[mint] failed , {result}')
        except Exception as e:
            print_red(f"[loop status error] {e}")
    except Exception as e:
        print_red(f"[main error] {e}")




if __name__ == "__main__":
    print_red('[main] start')
    while True:
        main()
        print_blue(f'[main] time : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
        time.sleep(3)
