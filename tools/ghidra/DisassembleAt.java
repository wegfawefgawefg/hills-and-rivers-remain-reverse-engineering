// Print every instruction in one or more functions selected by address.
// @category HillsAndRiversRemain

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class DisassembleAt extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] arguments = getScriptArgs();
        if (arguments.length == 0) {
            throw new IllegalArgumentException("usage: DisassembleAt.java ADDRESS [...]");
        }

        for (String argument : arguments) {
            Address address = toAddr(argument);
            Function function = getFunctionAt(address);
            if (function == null) {
                function = getFunctionContaining(address);
            }
            if (function == null) {
                println("NO FUNCTION AT " + address);
                continue;
            }

            println("===== " + function.getName(true) + " @ "
                    + function.getEntryPoint() + " =====");
            InstructionIterator instructions = currentProgram.getListing()
                    .getInstructions(function.getBody(), true);
            while (instructions.hasNext() && !monitor.isCancelled()) {
                Instruction instruction = instructions.next();
                println(instruction.getAddress() + "  " + instruction);
            }
        }
    }
}
