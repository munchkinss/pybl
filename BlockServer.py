from uuid import uuid4
import requests
from flask import Flask,jsonify,request
from Block import Block
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
