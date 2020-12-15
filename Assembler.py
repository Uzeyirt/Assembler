#Dictionaries for the instructions and the registers:
#Since the opcode is zero for all R-format instructions,
#Func:
R_Format = {
    "add"  : "100000", "move" : "100000",  # move -> add t1, t2, zero
    "slt"  : "101010", "sll"  : "000000",
    "jr"   : "001000"
}

#Opcode:
I_Format = {
    "addi" : "001000", "sw"   : "101011",
    "lw"   : "100011", "beq"  : "000100",
    "bne"  : "000101", "slti" : "001010"
}

J_Format = {
    "j"   : "000010", "jal" : "000011"
}

Registers = {
    "zero" : "00000", "at" : "00001", "v0" : "00010", "v1" : "00011",
    "a0"   : "00100", "a1" : "00101", "a2" : "00110", "a3" : "00111",
    "t0"   : "01000", "t1" : "01001", "t2" : "01010", "t3" : "01011",
    "t4"   : "01100", "t5" : "01101", "t6" : "01110", "t7" : "01111",
    "s0"   : "10000", "s1" : "10001", "s2" : "10010", "s3" : "10011",
    "s4"   : "10100", "s5" : "10101", "s6" : "10110", "s7" : "10111",
    "t8"   : "11000", "t9" : "11001", "k0" : "11010", "k1" : "11011",
    "gp"   : "11100", "sp" : "11101", "fp" : "11110", "ra" : "11111"
}

Labels = {}
current_address = 0
import sys, getopt

def R_FormatConverter(inst):
    operation = inst[0]
    opcode = "000000"
    rd = inst[1]
    rd = Registers.get(rd)
    if operation == "move":
        rs = inst[2]
        rs = Registers.get(rs)
        rt = Registers.get("zero")
        shamt = "00000"
    elif operation == "jr":
        func =  R_Format.get(operation)
        convert = opcode + rd + func.zfill(21)
        return convert
    elif operation == "sll":
        shamt = inst[3]        
        shamt = bin(int(shamt))
        shamt = shamt[2:]
        #shamt have to be 5-bit:
        if len(shamt) > 5:
            #if shift amount is longer than 5 bits, we can say it is 11111
            shamt = "11111"
        else:
            #we need to extend it with zeros in order to have a 5-bit shamt
            shamt = shamt.zfill(5)
        rs = "00000"
        rt = inst[2]
        rt = Registers.get(rt)
        func =  R_Format.get(operation)
        convert = opcode + rs + rt + rd + shamt + func
    else:
        shamt = "00000"
        rs = inst[2]
        rs = Registers.get(rs) 
        rt = inst[3]
        rt = Registers.get(rt) 
 
    func =  R_Format.get(operation)
    convert = opcode + rs + rt + rd + shamt + func
    return convert

def I_FormatConverter(inst):
    operation = inst[0]
    opcode = I_Format.get(operation)
    if inst[2].find("(") != -1:        
        #operation is store or load. it has addres with an offset
        #need to parse it in a different way -> 
        temp = inst[2].strip(")").split("(")
        offset = temp[0]
        base = temp[1]
        base = Registers.get(base) 
        rt = inst[1]
        rt = Registers.get(rt) 
        #convert offset to binary
        #the case where offset is positive
        if int(offset) >= 0:
            offset = bin(int(offset))
            offset = offset[2:].zfill(16)

        #the case where offset is negative
        else:
            offset = bin(int(offset))
            offset = offset[3:].zfill(16)
         
            #using 2's compliment
            offset = bin(int("1111111111111111", 2) - int(offset, 2) + int("0000000000000001", 2))
            offset = offset[2:]
        convert = opcode + base + rt + offset
        return convert
    else:
        #Instruction might be conditional (beq, bne) or an immediate such as addi
        #In addi, there will be a 16-bit constant instead of offset
        #For branch operations program calculates branch offset

        if inst[0] == "bne" or inst[0] == "beq":
            #Operation is branch
            rt = inst[1]
            rt = Registers.get(rt) 
            rs = inst[2]
            rs = Registers.get(rs)

            #calculating branch offset
            branch_target = Labels.get(inst[3])
            offset = bin((int(branch_target, 2) - current_address))
            if offset[0] == "-":
                offset = offset[3:].zfill(16)
         
                #using 2's compliment
                offset = bin(int("1111111111111111", 2) - int(offset, 2) + int("0000000000000001", 2))
                offset = offset[2:]
            else:
                offset = offset[2:].zfill(16)
            convert = opcode + rs + rt + offset
            return convert

        else:    
            #Instruction has an immediate field
            rt = inst[1]
            rt = Registers.get(rt) 
            rs = inst[2]
            rs = Registers.get(rs) 
            immediate = inst[3]
            #convert immediate to binary
            #the case where immediate is negative
            if '-' in immediate :
                immediate = bin(int(immediate[1:]))
                immediate = immediate[2:].zfill(16)
                #using 2's compliment
                immediate = bin(int("1111111111111111", 2) - int(immediate, 2) + int("0000000000000001", 2))
                immediate = immediate[2:]               
            #the case where immediate is positive
            else:
                immediate = bin(int(immediate))
                immediate = immediate[2:].zfill(16)
                

            convert = opcode + rs + rt + immediate
            return convert

def J_FormatConverter(inst):
    opcode = J_Format.get(inst[0])
    target = inst[1]
    if isinstance(target, int):
        #convert target to binary
        target = bin(int(target))
        target = target[2:].zfill(26)
    else:
        #target is label. need to find label's address
        target = Labels.get(target)
        target = target.zfill(26)
         
    convert = opcode + target
    return convert 

def find_Labels(fname):
    global current_address
    try:
        with open(fname, "r") as inFile:
            data = inFile.readlines()
            for line in data:
                if line.find(":") != -1:
                    new_label = line.split(":")
                    new_label = new_label[0]
                    #convert current address to binary
                    val = bin(current_address)
                    val = val[2:]
                    Labels.update({new_label : val})
                current_address += 4
    except IOError as e:
        print ("Operation failed: %s" % e.strerror)
    
    current_address = 0


def main(argv):
    # address of the first line of the program
    arguments = len(sys.argv) - 1
    global current_address
    if arguments == 0:
        #interactive mode
        line = input("Enter MIPS instruction: ")
        line = line.replace("$", "")
        line = line.replace(",", "")

        #If line contains any label, program adds it to the Labels dictionary with its address.
        #Then parses line and sends instruction to the functions
        if line[0].find(":") != -1:
            new_label = line[0]
            new_label = new_label.replace(":", "")
            val = bin(current_address)
            val = val[2:]
            Labels.update({new_label : val})
            instruction = line[1:]
            instruction = instruction.strip().split()
            operation = instruction[0]
            #first update current address
            current_address += 4
            if operation in R_Format.keys():
                convert = R_FormatConverter(instruction)
                print (convert)
            elif operation in I_Format.keys():
                convert = I_FormatConverter(instruction)
                print (convert)
            elif operation in J_Format.keys():
                convert = J_FormatConverter(instruction)
                print (convert)
            else:
                print("Invalid instruction.")
                sys.exit(0)

        else:
            #first update current address
            current_address += 4
            instruction = line.strip().split()
            operation = instruction[0]
            if operation in R_Format.keys():
                convert = R_FormatConverter(instruction)
                print (convert)
            elif operation in I_Format.keys():
                convert = I_FormatConverter(instruction)
                print (convert)
            elif operation in J_Format.keys():
                convert = J_FormatConverter(instruction)
                print (convert)
            else:
                print("Invalid instruction.")
                sys.exit(0)


    elif arguments == 2:  
        #batch mode
        #Firstly, need to find all labels in the file.
        find_Labels(sys.argv[1])
        try:
            with open(sys.argv[1], "r") as inFile, open(sys.argv[2], "w") as outFile:
                data = inFile.readlines()
                for line in data:
                    line = line.split("#")
                    line = line[0]
                    if len(line) == 0:
                        line = None
                        continue
                    line = line.replace("$", "")
                    #if line contains a label
                    if line.find(":") != -1:
                        line = line.strip().split(":")
                        line = line[1]
                    line = line.strip().split()
                    temp = []
                    for k in line:
                        k = k.strip().split(',')
                        for j in k:
                            if(j != ''): 
                                temp.append(j)
                    line = temp

                    operation = line[0]
                    if operation in R_Format.keys():
                        convert = R_FormatConverter(line)
                        outFile.writelines(convert + "\n")
                    elif operation in I_Format.keys():
                        convert = I_FormatConverter(line)
                        outFile.writelines(convert + "\n")
                    elif operation in J_Format.keys():
                        convert = J_FormatConverter(line)
                        outFile.writelines(convert + "\n")
                    else:
                        print("Invalid instruction.")
                        sys.exit(0)
                    current_address += 4  


        except IOError as e:
               print ("Operation failed: %s" % e.strerror)
    else:
        print("Interactive mode: sourceFile.py \nBatch mode: sourceFile.py inputFile.src outputFile.obj")
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)



