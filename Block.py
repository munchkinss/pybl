import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask,jsonify,request
class Block(object):
    def __init__(self):
        self.chain=[]
        self.current_transaction=[]
        self.node=set()
        self.psudohashcode={}
        self.new_block(previous_hash=None,proof=100)
        
    def register_node(self,address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """
        parsedurl=urlparse(address)
        if parsedurl.netloc:
            self.node.add(parsedurl.netloc)
        elif parsedurl.path:
            self.node.add(parsedurl.path)
        else:
            raise ValueError('INVALID URL')
    def valid_chain(self,chain):
        last_block=chain[0]
        current_index=1
        while current_index<len(chain):
            block=chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            last_block_hash=self.hash(last_block)
            if block['previous_hash']!=last_block_hash:
                return False
            if not self.valid_proof(last_block['proof'],block['proof'],last_block_hash):
                return False
            last_block=block
            current_index+=1
        return True
    def consensus_conflict(self):
        neighbours=self.node
        new_chain=None

        max_length=len(self.chain)

        for node in neighbours:
            response=request.get(f'http://{node}/chain')
            if response.status_code==200:
                length=response.json()['length']
                chain=response.json()['chain']
            if length>max_length and self.valid_chain(chain):
                max_length=length
                new_chain=chain
            if new_chain:
                self.chain=new_chain
                return True
            return False

    def new_block(self,proof,previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        if(previous_hash is None):
            self.psudohash(self,proof)
        block={
            'index':len(self.chain)+1,
            'timeStamp':time(),
            'transaction':self.current_transaction,
            'proof':proof,
            'previous_hash':previous_hash or self.psudohashcode
        }
        self.current_transaction=[]
        self.chain.append(block)
        return block
        
    @staticmethod
    def hash(block):
        
        block_string=json.dumps(block,sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    @staticmethod
    def psudohash(self,proof):
        psudoblock={
            'index':len(self.chain)+1,
            'timeStamp':time(),
            'transaction':self.current_transaction,
            'proof':proof,
        }
        self.psudohashcode=hashlib.sha256(json.dumps(psudoblock,sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]
    def new_transaction(self,sender,recipient,amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        self.current_transaction.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount
        })
        return self.last_block['index']+1
    def proof_of_work(self,last_block):
        last_proof=last_block['proof']
        last_hash=self.hash(last_block)

        proof=0

        while self.valid_proof(last_proof,proof,last_hash) is False:
            proof+=1
           
        return proof
    @staticmethod
    def valid_proof(last_proof,proof,last_hash):
        guess=f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash=hashlib.sha256(guess).hexdigest()
        return guess_hash[:4]=="0000"


app=Flask(__name__)

node_identifier=str(uuid4()).replace('-','')

blockchain=Block()

@app.route('/mine',methods=['GET'])
def mine():
    
    last_block=blockchain.last_block
    
    proof=blockchain.proof_of_work(last_block)

    blockchain.new_transaction(sender="0",recipient=node_identifier,amount=1,)
    previous_hash=blockchain.hash(last_block)
    block=blockchain.new_block(proof,previous_hash)
    response={
        'message':"NEW BLOCK CREATED",
        'index':block['index'],
        'transaction':block['transaction'],
        'proof':block['proof'],
        'previous_hash':block['previous_hash'],
    }
    return jsonify(response),200
@app.route('/transaction/new',methods=['POST'])
def new_transaction():
    values=request.get_json()
    required=['sender','recipient','amount']
    if not all(k in values for k in required):
        return "MISSING VALUES",400
    
    index=blockchain.new_transaction(values['sender'],values['recipient'],values['amount'])

    response={'message':f'Transaction will be added to Block {index}'}

    return jsonify(response),201

@app.route('/chain',methods=['GET'])
def full_chain():
    response={
        'chain':blockchain.chain,
        'length':len(blockchain.chain)
    }
    return jsonify(response),200

@app.route('/nodes/register',methods=['POST'])
def register():
    values=request.get_json()

    nodes=values.get('nodes')

    if nodes is None:
        return "Error:Please Supply a valid list of Nodes",400
    for Node in nodes:
        blockchain.register_node(Node)
    
    response={
        'message':'new NODE have been registed',
        'total_nodes':len(blockchain.node)
    }

    return jsonify(response),201

@app.route('/nodes/resolve',methods=['GET'])
def Consensus():
    replaced=blockchain.consensus_conflict()

    if replaced:
        response={
            "message":"our chain is replaced",
            "chain":blockchain.chain
        }
    else:
        response={
            "message":"our chain is authoritative",
            "chain":blockchain.chain
        }
    return jsonify(response),200

if __name__== '__main__':
    from argparse import ArgumentParser

    parser=ArgumentParser()

    parser.add_argument('-p','--port',default=5000,type=int,help='port to listen on')

    args=parser.parse_args()
    
    port=args.port

    app.run(host='0.0.0.0',port=port)
