from openai import OpenAI
from utils import *


### INITIAL PROMPT ###

# This will create the overall first prompt by either querying the user for contstaints and specs or will load already created ones
prompt = '''I would like you to help me code, I will provide a list of specifications of what the program will do and a list of constraints that it must abide by,
please reply with just code:
'''

# Has user choose a session name, if it already exists gives the option to start with previously generated code, otherwise creates appropriate folders
name, code, starting_iteration = pick_name()

# Generates the initial prompt, if dir is given then it will try to load, if unable it will have the user give constraints and specs for the program and save them in dir
conditions = get_conditions(dir="prompts/"+name+".txt")

# Adds the given/loaded conditions to the basic prompt to create the "orginal prompt", which will be used throughout 
original_prompt = prompt + conditions

### TODO Get the model to adjust the prompts ###


### CODE GENERATION LOOP ###

mode = "auto"
# mode = 'human'

for iteration in range(5):
    code = gen_code(iteration+starting_iteration, original_prompt, code, name, mode=mode)

    if iteration % 8 == 0 and iteration > 0:
        human_eval = get_human_eval(remove_code_block(code))
        original_prompt += "\nAlso abide by the following feedback:\n" + human_eval


# code = bug_test_and_fix(iteration+1, name, remove_code_block(code), max_tries=5)
code_usable = remove_code_block(code)

with open("code/"+name+"/final.py", 'w') as filetowrite:
    filetowrite.write(code_usable)

print("Done.")
print('Final Code saved in "code/'+name+'/final.py"')




