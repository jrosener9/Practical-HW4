from pyteal import *
from pyteal_helper import itoa


def approval_program():
    """APPROVAL PROGRAM handles the main logic of the application"""

    i = ScratchVar(TealType.uint64)  # i-variable for for-loop

    on_creation = Seq(
        [
            # TODO:
            # Check number of required arguments are present
            # Store relevant parameters of the election. When storing the options to vote for,
            # consider storing all of them as a string separated by commas e.g: "A,B,C,D".
            # Note that index-wise, A=0, B=1, C=2, D=3
            # Set all initial vote tallies to 0 for all vote options, keys are the vote options
            Assert(Txn.application_args.length() == Int(3)),
            App.globalPut(Bytes("ElectionEnd"), Btoi(Txn.application_args[0])),
            App.globalPut(Bytes("NumVoteOptions"), Btoi(Txn.application_args[1])),
            App.globalPut(Bytes("VoteOptions"), Txn.application_args[2]),

            For(
                i.store(Int(0)), i.load() < App.globalGet(Bytes('NumVoteOptions')), i.store(i.load() + Int(1)) 
            ).Do(
                App.globalPut(Concat(Bytes("VotesFor"), itoa(i.load())), Int(0))
            ),
            
            Return(Int(1)),
        ]
    )

    # call to determine whether the current transaction sender is the creator
    is_creator = Txn.sender() == Global.creator_address()

    # value of whether or not the sender can vote ("yes", "no", or "maybe")
    get_sender_can_vote = App.localGetEx(Int(0), App.id(), Bytes("can_vote"))

    get_user_can_vote = App.localGetEx(Txn.application_args[1], App.id(), Bytes("can_vote"))

    # get_vote_sender is a value that the sender voted for,
    #   a number indicating the index in the VoteOptions string faux-array.
    # Remember that since we stored the election's voting options as a string separated by commas (such as "A,B,C,D"),
    # If a user wants to vote for C, then the choice that the user wants to vote for is equivalent to the uint 2
    get_vote_of_sender = App.localGetEx(Int(0), App.id(), Bytes("voted"))

    on_closeout = Seq(
        # TODO: CLOSE OUT:
       [
        get_vote_of_sender,
        Assert(Global.round() <= App.globalGet(Bytes("ElectionEnd"))),
        If (
            get_vote_of_sender.hasValue(), 
            App.globalPut(
                    Concat(Bytes("VotesFor"), itoa(get_vote_of_sender.value())),
                    App.globalGet(Concat(Bytes("VotesFor"), itoa(get_vote_of_sender.value()))) - Int(1),
            )
        ), 
        Return(Int(1))
        ]
    )

    on_register = Seq(
        
        [
        Assert(Global.round() <= App.globalGet(Bytes("ElectionEnd"))), 
        App.localPut(Int(0), Bytes("can_vote"), Bytes('maybe')),
        Return(Int(1))
        ]
    )

    on_update_user_status = Seq(
        # TODO: UPDATE USER LOGIC

        [   
            get_user_can_vote, 
            Assert(is_creator), 
            Assert(Global.round() <= App.globalGet(Bytes("ElectionEnd"))), 
            Assert(get_user_can_vote.value() == Bytes('maybe')),
            App.localPut(Txn.application_args[1], Bytes('can_vote'), Txn.application_args[2]),
            Return(Int(1))
        ]
    )

    choice = Btoi(Txn.application_args[1])
    on_vote = Seq(
        # TODO: USER VOTING LOGIC:
        [
            get_vote_of_sender,
            get_sender_can_vote,
            Assert(Global.round() <= App.globalGet(Bytes("ElectionEnd"))), 
            Assert(get_sender_can_vote.value() == Bytes('yes')),
            Assert(get_vote_of_sender.hasValue() == Int(0)), 
            Assert(And(
                        choice < App.globalGet(Bytes("NumVoteOptions")), 
                        choice >= Int(0)
                    )
            ),
            Seq(
                App.localPut(Int(0), Bytes('voted'), choice), 
                App.globalPut(
                    Concat(Bytes("VotesFor"), itoa(choice)),
                    App.globalGet(Concat(Bytes("VotesFor"), itoa(choice))) + Int(1),
                )
            ), 
            Return(Int(1))
        ]
    )

    program = Cond(

        # MAIN CONDITIONAL

        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, on_register],
        [Txn.application_args[0] == Bytes("vote"), on_vote], 
        [Txn.application_args[0] == Bytes("update_user_status"), on_update_user_status]


        # TODO: Complete the cases that will trigger the update_user_status and on_vote sequences

    )

    return program


def clear_state_program():
    """ Handles the logic of when an account clears its participation in a smart contract. """

    # TODO: CLEAR STATE PROGRAM

    get_vote_of_sender = App.localGetEx(Int(0), App.id(), Bytes("voted"))

    program = Seq(
        # remove their vote from the correct vote tally
       [
        get_vote_of_sender,
        Assert(Global.round() <= App.globalGet(Bytes("ElectionEnd"))),
        If (
            get_vote_of_sender.hasValue(), 
            App.globalPut(
                    Concat(Bytes("VotesFor"), itoa(get_vote_of_sender.value())),
                    App.globalGet(Concat(Bytes("VotesFor"), itoa(get_vote_of_sender.value()))) - Int(1),
            )
        ), 
        Return(Int(1))
        ]
    )

    return program


if __name__ == "__main__":
    
    with open("vote_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)

    with open("vote_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
        f.write(compiled)
