from openai import OpenAI
import os
import glob

with open('../OPEN_AI_KEY.txt', 'r') as file: 
    key = file.read()

client = OpenAI(api_key=key)
model = "gpt-4"

def pick_name():

    name = input("what is the name of your project (will load if used previously)?")
    starter_code = None
    starting_iteration = 1

    # If the session name has already been used then this will give the option to restart with a code basis
    if os.path.exists("code/"+name+"/"):
        print("Session found! The following files were found with that project name:")
        file_list = os.listdir("code/"+name+"/")
        print(file_list)
        file = input("Which would you like to initialize? ('none' if you'd like to restart)")
        if file != 'none' and file in file_list:
            with open("code/"+name+"/"+file, 'r') as filetowrite:
               print("starting with code from: "+file )
               starter_code = filetowrite.read()
            
            if file != "final.py":
                starting_iteration = int(file[4]) + 1
            else:
                starting_iteration = len(file_list)

    # Creates all necessary folders if they didn't exist
    for dir in ["code/", "evals/", "bugs/"]:
        if not os.path.exists(dir+name+"/"):
            os.makedirs(dir+name+"/")

    
    return name, starter_code, starting_iteration

def remove_code_block(code):
    # Removes the ``` and python blocking that GPT creates
    code = code.replace("```", "")
    code = code.replace("python", "")

    return code


def get_conditions(dir=None):
# This will create the overall first prompt by either querying the user for contstaints and specs or will load already created ones

    if os.path.exists(dir):
        with open(dir, 'r') as file:
            return file.read()

    conditions = '''
    Constraints:

    1. Must be coded for Python 3.10
    2. Must run from a single function "main()", which may have input parameters
    3. Has to be able to run on a moderately powerful computer in under 1 minute
    4. There must be a method "close()", which takes no parameters and ends the program, interupting anything ongoing
    5. Has to be able to run on a moderately powerful computer in under 1 minute
    6. You may not assume that there are any outside files, e.g. you may not use png files 
    '''

    counter = 7
    cont = input("enter a constraint for your program or 'done' if finished:") 
    while not cont == 'done':
        conditions += "\t" + str(counter) +". " + cont + "\n"
        cont = input("enter a constraint for your program or 'done' if finished:")
        counter += 1 

    conditions += ('''

    Specifications:

    ''')

    counter = 1
    spec = input("enter a spec for your program or 'done' if finished:") 
    while not spec == 'done':
        conditions += "\t" + str(counter) +". " + spec + "\n"
        spec = input("enter a spec for your program or 'done' if finished:")
        counter += 1 

    # Save prompt for future use
    with open(dir, 'w') as filetowrite:
        filetowrite.write(conditions)

    return conditions

def get_human_eval(code):

    # Runs the code for human evaluation
    # The user will be prompted to give a list of things for the ai to change

    with open("testing.py", 'w') as filetowrite:
        filetowrite.write(remove_code_block(code))

    try:
        import testing
        testing.main()
        testing.close()
    except Exception as e:
        print("crashed with exception: " + str(e))

    human_eval = ''''''

    counter = 1
    feedback = input("what needs to change? ('done' to stop)")
    while feedback != "done":
        human_eval += str(counter) + feedback + "\n"
        feedback = input("what else? ('done' to stop)")
        counter += 1
    
    return human_eval



def gen_self_eval(iteration, original_prompt, code, name):
    # Generates a self evaluation based on a given prompt + conditions and already generated code
    # The model will return just a list of changes it thinks should be made

    print("generating self evaluation...")

    evaluation_prompt = ''' I would like you to consider the following prompt and code. Please create a short list of changes that would improve the code's adherence to the prompt. 
    The list should be specific code changes, not and should not just be a paraphrasing of the original prompt. Your response should only be a list with no code:

    PROMPT:
    ''' + original_prompt + '''CODE:
    ''' + code

    response = client.chat.completions.create(
    model=model,
    messages=[{"role":"system", "content":evaluation_prompt}]
    )

    with open("evals/"+name+"/eval"+str(iteration-1)+".txt", 'w') as filetowrite:
        filetowrite.write(response.choices[0].message.content)

    return response.choices[0].message.content

def gen_code(iteration, original_prompt, code=None, name="code", mode="auto"):
    # Using a prompt, which may be an evaluation or original prompt + conditions create new code that will satisfy the original prompt

    print("generating number " + str(iteration) + " iteration of code...")

    if code is not None:

        if mode == "auto":
            evaluation = gen_self_eval(iteration, original_prompt, code, name)
        elif mode == "human":
            evaluation = get_human_eval(code)

        prompt = '''I would like you to change this code:
        ''' + code + '''

        Such that it adheres to these changes: 
        ''' + evaluation + '''

        The modified code should also complete any previously created methods which have not been fully implemented and should not remove them.
        You MUST not include anything aside from the code itself
        '''
    elif iteration > 1:
        # We can start in a later iteration if we so choose
        with open("code/code"+str(iteration-1)+".py", 'r') as filetowrite:
            code = filetowrite.read()
        return gen_code(iteration, original_prompt, code)
    else:
        prompt = original_prompt

    response = client.chat.completions.create(
    model=model,
    messages=[{"role":"system", "content":prompt}]
    )

    code = response.choices[0].message.content
    code_usable = remove_code_block(code)


    with open("code/"+name+"/code"+str(iteration)+".py", 'w') as filetowrite:
        filetowrite.write(code_usable)
    
    return code

def try_code_get_errors(code):
    # Tests the code and returns the error raised as a string if any were
    # This is used to reprompt to fix bugs


    with open("testing.py", 'w') as filetowrite:
        filetowrite.write(code)

    try:
        import testing
        testing.main()
        testing.close()
    except Exception as e:
        return str(e)

def bug_test_and_fix(iteration, name, code=None, tries=1, max_tries=3):

    print("Bug test number " + str(iteration) + ", try number:"+str(tries)+"...")

    # Get code if not passed
    if code is None:
        with open("code/"+name+"/code"+str(iteration)+".py", 'r') as filetowrite:
            code = filetowrite.read()

    # Test for an exception (not full testing)    
    bug = try_code_get_errors(code)

    # Save the bug for later reference
    with open("bugs/"+name+"/bug"+str(iteration)+".txt", 'w') as filetowrite:
        if bug is None:
            filetowrite.write("None found")
        else:
            filetowrite.write(bug)
    

    if bug is None:
        print("Main and close methods ran without exception")
        return code
    
    if tries <= max_tries and bug is not None:
        print("Exception found! Squashing")

        bug_fix_prompt = '''I would like you to please help me debug my code, given the following exception and code please fix the error so that this excpetion is no longer raised:
        
        Exception: 

        ''' + bug + '''

        Code: 
        
        ''' + code + '''

        Your response must only be code. It should be the original code modified to fix the error.
        '''

        response = client.chat.completions.create(
        model=model,
        messages=[{"role":"system", "content":bug_fix_prompt}]
        )

        code = response.choices[0].message.content
        code_usable = remove_code_block(code)

        return bug_test_and_fix(iteration, name, code_usable, tries+1)
    else:
        print("3 attempts made to debug, abandoning :/")
        return code