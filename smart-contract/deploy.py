from algosdk.future import transaction
from algosdk import account, mnemonic
from secrets import account_mnemonics, algod_headers, algod_address
from election_params import local_ints, local_bytes, global_ints, \
    global_bytes, num_vote_options, vote_options, relative_election_end

from election_smart_contract import approval_program, clear_state_program
from helper import compile_program, int_to_bytes, read_global_state, wait_for_confirmation
from pyteal import compileTeal, Mode, Bytes
from algosdk.v2client import algod

# Define keys, addresses, and token
account_private_keys = [mnemonic.to_private_key(mn) for mn in account_mnemonics]
account_addresses = [account.address_from_private_key(sk) for sk in account_private_keys]

# Declare application state storage for local and global schema
global_schema = transaction.StateSchema(global_ints, global_bytes)
local_schema = transaction.StateSchema(local_ints, local_bytes)


def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema, app_args):
    """
    Create a new application from the compiled approval_program, clear_program
    using the application arguments app_args
    Return the newly created application ID
    """
    # TODO: define sender as creator
    # TODO: declare the on_complete transaction as a NoOp transaction
    # TODO: get node suggested parameters
    # TODO: create unsigned transaction
    # TODO: sign transaction
    # TODO: send transaction
    # TODO: await confirmation

    sender = account.address_from_private_key(private_key)
    on_complete = transaction.OnComplete.NoOpOC.real  
    params = client.suggested_params() 


    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
        app_args,
    )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 5)
        print("TXID: ", tx_id)
        print(
            "Result confirmed in round: {}".format(
                transaction_response["confirmed-round"]
            )
        )
    except Exception as err:
        print("Here is the error")
        print(err)
        return 0

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response["application-index"]
    print("Created new app-id:", app_id)

    return app_id


def create_vote_app(client, creator_private_key, election_end, num_vote_options, vote_options):
    """
    Create/Deploy the voting app
    This function uses create_app and return the newly created application ID
    """
    # TODO:
    # Get PyTeal approval program
    # compile program to TEAL assembly
    # compile program to binary
    # Do the same for PyTeal clear state program
    # TODO: Create list of bytes for application arguments and create new application. 
    approval_program_ast = approval_program()
    approval_program_teal = compileTeal(
        approval_program_ast, mode=Mode.Application, version=5
    )
    approval_program_compiled = compile_program(client, approval_program_teal)

    # get PyTeal clear state program
    clear_state_program_ast = clear_state_program()
    # compile program to TEAL assembly
    clear_state_program_teal = compileTeal(
        clear_state_program_ast, mode=Mode.Application, version=5
    )
    # compile program to binary
    clear_state_program_compiled = compile_program(
        client, clear_state_program_teal
    )


    # create list of bytes for app args
    app_args = [
        int_to_bytes(election_end),
        int_to_bytes(num_vote_options),
        vote_options.encode(),
    ]

    app_id = create_app(
        client,
        creator_private_key,
        approval_program_compiled,
        clear_state_program_compiled,
        global_schema,
        local_schema,
        app_args,
    )

    return app_id


def main():
    # TODO: Initialize algod client and define absolute election end time fom the status of the last round.
    # TODO: Deploy the app and print the global state.
    client = algod.AlgodClient(
        algod_token="WTKXJ8WsLa14pDEiXXJgt9EXRW7p0B8be3WSQfI1",
        algod_address="https://testnet-algorand.api.purestake.io/ps2",
        headers={"X-API-Key": "WTKXJ8WsLa14pDEiXXJgt9EXRW7p0B8be3WSQfI1"}
    )

    last_round = client.status().get("last-round")
    app_id = create_vote_app(client, account_private_keys[0], last_round+relative_election_end, num_vote_options, vote_options)
    print("Global state:", read_global_state(client, app_id))

    pass


if __name__ == "__main__":
    main()
