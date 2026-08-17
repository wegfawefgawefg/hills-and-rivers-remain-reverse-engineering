// Decompile one or more functions by address and print reproducible output.
// @category HillsAndRiversRemain

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

public class DecompileAt extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] arguments = getScriptArgs();
        if (arguments.length == 0) {
            throw new IllegalArgumentException("usage: DecompileAt.java ADDRESS [...]");
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException(decompiler.getLastMessage());
        }

        try {
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

                println("===== " + function.getName(true) + " @ " + function.getEntryPoint() + " =====");
                DecompileResults results = decompiler.decompileFunction(function, 120, monitor);
                if (!results.decompileCompleted()) {
                    println("DECOMPILE FAILED: " + results.getErrorMessage());
                    continue;
                }
                println(results.getDecompiledFunction().getC());
            }
        } finally {
            decompiler.dispose();
        }
    }
}
