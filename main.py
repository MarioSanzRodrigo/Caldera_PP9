import sqlite3
import webbrowser
import SequentialRandomModel
import getStatusOp
import random_words_gen
import os
import sys
import yaml
import json
import uuid
import argparse
import random
import subprocess
import time
import socket
import requests
import re
import math

#########################################################################################

payload={"username": "admin", "password": "admin", "rememberMe": True}
url = "http://localhost:8888"
x = 'false'

option = ''
tactics = []
tacticNames = []
tacticNumber = []
dataSoures = []
dataSourceList = []
OpIDs = []
tacticResults = []

intrusionSetId = []
intrusionSetCreated = []
intrusionSetModified = []
intrusionSetName = []
intrusionSetDescription = []
aliases = []
intrusionSetNameList = []

attackList = []
attackPatternTypes = []
attackPatternId = []
attackPatternCreated = []
attackPatternModified = []
attackPatternNames = []
attackPatternDescriptions = []
attackPatternPhaseNames = []
attackPatternPhaseNumber = []

#########################################################################################

directory = os.getcwd()
directory = directory.replace("\\", "/")
db_file = directory + '/COBRA_ddbb.sqlite' # path to the local db file
conn = None

try:
    conn = sqlite3.connect(db_file)
except Error as e:
    print(e)


def finish_write_file(apt_name):
    '''
    Esta función elimina los caracteres finales del fichero para poder ser visualizado en STIX-Viewer.
    También añade los caracteres para cerrar el bundle que agrupa el conjunto de objetos STIX que componen el modelo.
    :param: apt_name: Nombre del grupo APT.
    :return: Terimna de escribir el archivo JSON que contiene el modelo del APT generado.
    '''
    print("---------------YOUR MODEL IS READY---------------\n")


def working_directories():
    workingPath = subprocess.check_output("pwd", shell=True)
    workingPath = str(workingPath)
    workingPath = workingPath[2:len(workingPath)-3]
    calderaPath = subprocess.check_output("find ~/ -type d -name 'caldera'", shell=True)
    calderaPath = str(calderaPath)
    calderaPath = calderaPath[2:len(calderaPath)-3]
    return [workingPath, calderaPath]


def operation_IDs(operationData):
    operationData = str(operationData)
    operationData = str(operationData[3:len(operationData)-2])
    operationData = re.sub(r'\\', ' ', operationData)
    print(operationData)
    operationDict = json.loads(operationData)
    operationID = operationDict['id']
    operationID = str(operationID)
    print("\nOperation ID: " + operationID + "\n")
    return operationID


def agent_PAWs(agentData):
    agentData = str(agentData)
    agentData = str(agentData[3:len(agentData)-2])
    print(agentData)
    agentDict = json.loads(agentData)
    agentPAW = agentDict['paw']
    agentPAW = str(agentPAW)
    print("\nAgent PAW: " + agentPAW + "\n")
    return agentPAW


def getOperationStatus(operationID, objective):
    subprocess.check_output("curl -X 'GET' " + '-H "KEY:ADMIN123" ' + "'http://localhost:8888/api/v2/operations/" + operationID + "' -H 'accept: application/json' >> informe.json", shell=True)
    statusFile = subprocess.check_output('cat informe.json', shell=True)
    statusFile = str(statusFile)
    matches = re.findall(r'status....',statusFile)
    matches.pop(0)
    with open('statusObjective.txt', 'w') as f:
        print(matches[objective-1], file = f)
    print(matches[objective-1])


def checkPause():
    with open('.env', 'r') as f:
        content = subprocess.check_output('cat .env', shell=True)
        content = str(content)
        content = content[2:len(content)-3]
        if 'APT=False' not in content:
            statusPause()
            

def statusPause():
    time.sleep(100)
    checkPause()


def createStatusFiles():
    with open('statusObjective.txt', 'w') as f:
        print('status": 3', file = f)


def createControlFiles(operationID):
    with open('PLAY_caldera.sh', 'w') as f:
        print('#!/bin/bash', file = f)
        print('cd /home/cobra/Apt_simulator/APTSIMULATOR', file = f)
        print("curl -X 'PATCH' -H " + '"KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/operations/" + operationID + "' -d '" + '{"state": "run_one_link", "auto_close": true' + "}'", file = f)
        print("sed -i 's/True/False/g' .env", file = f)
        f.close()

    with open('PAUSE_caldera.sh', 'w') as f:
        print('#!/bin/bash', file = f)
        print('cd /home/cobra/Apt_simulator/APTSIMULATOR', file = f)
        print("curl -X 'PATCH' -H " + '"KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/operations/" + operationID + "' -d '" + '{"state": "paused", "auto_close": true' + "}'", file = f)
        print("sed -i 's/False/True/g' .env", file = f)
        f.close()

    with open('GET_OperationState.sh', 'w') as f:
        print('#!/bin/bash', file = f)
        print('cd /home/cobra/Apt_simulator/APTSIMULATOR', file = f)
        print("curl -X 'GET' -H " + '"KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/operations/" + operationID + "' -H " + "'accept: application/json' >> informe.json", file = f)
        f.close()


def closeOperations(operationID, agentPAW):
    for operationID in OpIDs:
        os.system("curl -X 'DELETE' " +  '-H "KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/operations/" + operationID + "'")
    os.system("curl -X 'PATCH' " +  '-H "KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/agents/" + agentPAW + "' -d '" +  '{"watchdog": 1, "sleep_min": 3, "sleep_max": 3}' + "'\n")
    time.sleep(60)
    os.system("curl -X 'DELETE' " +  '-H "KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/agents/" + agentPAW + "'")
    os.system("pkill -f server.py")
    os.system("rm PLAY_caldera.sh")
    os.system("rm GET_OperationState.sh")
    os.system("rm PAUSE_caldera.sh")
    with open('.env', 'w') as f:
        print('APT=False', file = f)
    createStatusFiles()


def adversary_yaml_file(apt_name, attackPatternId, platform, timer, objective):
    #Generate Adversarie FILE

    paths = working_directories()
    workingPath = paths[0]
    calderaPath = paths[1]
    if apt_name in intrusionSetNameList:
        APTID = conn.cursor()
        APTID.execute("SELECT id FROM sdos_object WHERE name IS '"+ apt_name + "'")
        APTIDRows = APTID.fetchall()
        UUID = str(APTIDRows)
        UUID = UUID[3:len(UUID)-4]
        path_to_adversary_file = calderaPath + '/plugins/stockpile/data/adversaries/' + UUID + '.yml'
        print(path_to_adversary_file)
        os.system('cp -a ' + path_to_adversary_file + ' ' + workingPath)
        fileLines = os.system('wc -l < ' + UUID + '.yml')
        nAttackPatterns = fileLines - 6
        nAttackPatterns = abs(nAttackPatterns)
        timestop = timer/nAttackPatterns
        objective = nAttackPatterns - 1
        print(objective)

    else:
        UUID = str(uuid.uuid4())
        with open(UUID + '.yml', 'w') as f:
            print("Creating the adversary file: " + UUID + "\n")
            print('---', file = f)
            print('', file = f)
            print('id: ' + UUID, file = f)
            print('name: ' +  apt_name, file = f)
            print('description: description', file = f)
            print('atomic_ordering: ', file = f)
            i = 0
            nAttackPatterns = 0
            for act in attackPatternId:
                print('  - ' + str(act), file = f)
                nAttackPatterns = nAttackPatterns + 1
            timestop = timer/nAttackPatterns
            print('objective: 495a9828-cab1-44dd-a0ca-66e58177d8cc', file = f)
            print('adversary_id: ' + UUID, file = f)
            f.close()
    APTTimestop = timestop
    checkPause()
    run_operation_file(UUID, apt_name, nAttackPatterns, APTTimestop, objective)
    

def run_operation_file(UUID, apt_name, nAttackPatterns, timestop, objective):
    #Upload FILE
    createStatusFiles()
    paths = working_directories()
    workingPath = paths[0]
    calderaPath = paths[1]
    PATH = subprocess.check_output("find ~/ -type f -name '"+ UUID +".yml'", shell=True)
    PATH = str(PATH)
    PATH = PATH[2:len(PATH)-3]
    path_to_adversary_file = calderaPath + '/plugins/stockpile/data/adversaries/' + UUID + '.yml'
    file_exists = os.path.exists(path_to_adversary_file)
    if file_exists == False:
        os.system("mv "+ UUID + ".yml " + calderaPath + "/plugins/stockpile/data/adversaries/\n")

        #Decrypt FILE
        os.system("python3 " + calderaPath + "/app/utility/file_decryptor.py -k ADMIN123 -s REPLACE_WITH_RANDOM_VALUE " + calderaPath +"/plugins/stockpile/data/adversaries/" + UUID + ".yml")
        os.system("mv " + calderaPath + "/plugins/stockpile/data/adversaries/" + UUID + ".yml_decrypted " + calderaPath + "/plugins/stockpile/data/adversaries/" + UUID + ".yml\n")

    #Update CALDERA (Reboot CALDERA)
    os.system("pkill -f server.py")
    os.chdir(calderaPath)
    os.system('python3 server.py --insecure 2>&1 &')
    os.chdir(workingPath)
    print("\nCALDERA running...\n")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client.connect(('0.0.0.0', 8888))
            break
        except Exception as e:  
            print("Retrying:", e);
            time.sleep(10)
    with requests.Session() as s:
        response_op = s.post(url, json=payload)
        print("\nConnected to CALDERA server...\n")
    time.sleep(10)
    queryAgents = ''
    print("Connecting to agent...\n")
    while '[{' not in queryAgents:
        agentData = subprocess.check_output('curl -X GET -H "KEY:ADMIN123" "http://0.0.0.0:8888/api/v2/agents" -H "accept: application/json"', shell=True)
        queryAgents = str(agentData)
        time.sleep(5)
        if '[{' in queryAgents:
            agentPAW = agent_PAWs(agentData) 
            break
    print("Agent connected\n")

    #Running autonomous operation
    operationData = subprocess.check_output('curl -X PUT -H "KEY:ADMIN123" http://0.0.0.0:8888/api/rest -d ' + "'{" + '"index":"operations", "name":"Operation_' + apt_name.upper() + '", "state":"running", "auto_close": true, "adversary_id": "'+ UUID +'"}' + "'\n", shell=True)
    print("Running Operation: " + apt_name.upper()+ "\n")
    operationID = operation_IDs(operationData)
    OpIDs.append(operationID)
    createControlFiles(operationID)
    
    #Report extraction
    path_to_report = "/tmp/event_logs/operation_" + operationID + ".json"
    while True:
        file_exists = os.path.exists(path_to_report)
        if file_exists == True:
            print(objective)
            os.system("mv " + path_to_report + " " + workingPath + "/operation_" + operationID + ".json")
            print("File saved\n")

            #Running timestep operation
            checkPause()
            operationData = subprocess.check_output('curl -X PUT -H "KEY:ADMIN123" http://0.0.0.0:8888/api/rest -d ' + "'{" + '"index":"operations", "name":"Operation_' + apt_name.upper() + '", "state":"run_one_link", "auto_close": true, "adversary_id": "'+ UUID +'"}' + "'\n", shell=True)
            print("Running timestep operation\n")
            operationID = operation_IDs(operationData)
            OpIDs.append(operationID)
            createControlFiles(operationID)
            operationCounter = 1
            while operationCounter < nAttackPatterns:
                checkPause()
                time.sleep(timestop)
                checkPause()
                changeStateOp = os.system("curl -X 'PATCH' -H " + '"KEY:ADMIN123" ' + "'http://0.0.0.0:8888/api/v2/operations/" + operationID + "' -d '" + '{"state": "run_one_link", "auto_close": true' + "}'\n")
                print(" ")
                operationCounter = operationCounter + 1
            break
        else:
            print("Waiting for operation file...")
            time.sleep(30)
    path_to_report = "/tmp/event_logs/operation_" + operationID + ".json"
    while True:
        file_exists = os.path.exists(path_to_report)
        if file_exists == True:
            getOperationStatus(OpIDs[1], objective)
            closeOperations(operationID, agentPAW)
            break


def choose_parameters():
    '''
    Esta función muestra la cadena de preguntas que se realizarán al usuario para definir los parámetros configurables del modelo secuencial de APTs aleatorios.
    :return: total_params: Lista que contiene los parámetros elegidos por el usuario.
    '''
    total_params = []
    apt_name = ''
    platform = ''
    objective = ''
    question_apt_group_name = str(input('Do you want to set the APT Group name? If you say no, a randomly generated APT Group name will be assigned. Yes/No: ')).lower()
    if question_apt_group_name == 'yes':
        if option == 1:
            print("Available names: ", intrusionSetNameList)
            name = str(input('Write the name of the APT Group: '))
            if name in intrusionSetNameList:
                apt_name = name
            else:
                print("Wrong APT Group name")
                return
        else:
            apt_name = str(input('Write the name of the APT Group: '))
    if question_apt_group_name == 'no':
        if option == 1:
            apt_name = random.choice(show_threat_actors())
        else:
            apt_name = random_words_gen.pick_two_random_words()

    if option == 2:
        question_plat = str(input('Do you want to configure a specific target platform? If you say no, a random platform will be assigned. Yes/No: ')).lower()
        if question_plat == 'yes':
            platforms = SequentialRandomModel.get_platforms_of_attacks()
            print("Available platforms: ", platforms)
            plat = str(input('Write the name of the platform: '))
            if plat in platforms:
                platform = plat
            else:
                print("Wrong platform")
                return
        if question_plat == 'no':
            platforms = random.choice(SequentialRandomModel.get_platforms_of_attacks())
            platform = platforms
        question_Objective = str(input('Do you want to configure a specific objective? Yes/No: ')).lower()
        if question_Objective == 'yes':
            objectives = SequentialRandomModel.get_objectives_of_attacks()
            print("Available objectives: ", objectives)
            objec = int(input('Write the number of the objective: '))
            obj = objectives[objec]
            obj = str(obj)
            if 3 <= objec <= 14:
                objective = obj
            else:
                print("Wrong objective")
                return
        if question_Objective == 'no':
            objectives = SequentialRandomModel.get_objectives_of_attacks()
            objective = objectives[random.randint(3, 14)]

    total_params.append(apt_name)
    total_params.append(platform)
    total_params.append(objective)
    print('\nThe selected parameters are: ', total_params)
    return total_params


def generate_parameters():
    '''
    Esta función muestra el proceso de definición de los parámetros configurables del modelo secuencial de APTs reales, en caso de que el ususario decida no configurar dichos parámetros.
    :return: total_params: Lista que contiene los parámetros elegidos por el usuario.
    '''
    total_params = []
    apt_name = ''
    platform = ''
    objective = ''
    timer = 0
    if option == 1:
        apt_name = random.choice(show_threat_actors())
    else:
        apt_name = random_words_gen.pick_two_random_words()
        platform = random.choice(SequentialRandomModel.get_platforms_of_attacks())
        objectives = SequentialRandomModel.get_objectives_of_attacks()
        objective_num = random.randint(1, 14)
        objective = objectives[objective_num]

    total_params.append(apt_name)
    total_params.append(platform)
    total_params.append(objective_num)
    return total_params


def show_threat_actors():
    '''
    Esta función devuelve todos los actores de amenazas (grupos APTs) que se encuentran actualmente en la matriz enterprise de MITRE ATT&CK.
    :return: intrusionSetNameList: Listado de los nombres (aliases) de todos los gurpos APT registrados.
    '''
    intrusionSetListCur = conn.cursor()
    intrusionSetListCur.execute("SELECT alias FROM aliases INNER JOIN sdos_object so ON aliases.fk_object_id = so.id GROUP BY fk_object_id ORDER BY alias")
    intrusionSetListRows = intrusionSetListCur.fetchall()

    i = 0
    for row in intrusionSetListRows:
        intrusionSetNameList.append(row[0])
        i = i + 1
    return(intrusionSetNameList)


menu_options = {
    1: 'Generate a real sequential APT model',
    2: 'Generate a random sequential APT model',
    3: 'Open STIX Visualizer',
    4: 'About',
    5: 'Exit',
}


def print_menu():
    '''
    Esta función saca por pantalla el menú principal del programa.
    :return: String cabecera de la plataforma de simulación.
    '''
    print("--**--**--**--**--**--**--**--**--**--**--*")
    print("              HI THERE HACKER!             ")
    print("     WELCOME TO THE APT MODEL GENERATOR    ")
    print("--**--**--**--**--**--**--**--**--**--**--*\n")
    print("What do you want to do?\n")
    for key in menu_options.keys():
        print(key, '->', menu_options[key])


def option1():
    '''
    Esta opción genera un modelo secuencial APT real, con la opción de configurar parámetros aleatorios o no.
    :return: modelo secuencial de un APT real generado.
    '''
    try:
        if intrusionSetNameList == []:
            show_threat_actors()
        print("Let's generate a real APT model\n")
        opt = str(input('Do you want to configure some of the parameters? Yes/No: ')).lower()
        if opt == 'yes':
            try:
                print("Let's configure some parameters together :)")
                chosen_params = choose_parameters()
                adversary_yaml_file(chosen_params[0], attackPatternId, chosen_params[2], chosen_params[1], )
                print("\nHow difficult do you want it to be?")
                print("1 - Be kind please (Easy)")
                print("2 - Let's give it a try (Medium)")
                print("3 - Go hard or go home! Show me what you got! (Hard)")
                level = int(input('\nChoose a level of difficulty: '))
                if level == 1:
                    print("EASY")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 2:
                    print("MEDIUM")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 3:
                    print("HARD")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                else:
                    print('ERROR: Wrong level. Please select a level between 1 and 3')
                    return
                finish_write_file(chosen_params[0])
            except Exception as ex:
                print(ex)
                print("ERROR: Could not create the real APT model with those parameters")
        elif opt == 'no':
            try:
                chosen_params = generate_parameters()
                adversary_yaml_file(chosen_params[0], attackPatternId, chosen_params[2])
                print("\nHow difficult do you want it to be?")
                print("1 - Be kind please (Easy)")
                print("2 - Let's give it a try (Medium)")
                print("3 - Go hard or go home! Show me what you got! (Hard)")
                level = int(input('\nChoose a level of difficulty: '))
                if level == 1:
                    print("EASY")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 2:
                    print("MEDIUM")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 3:
                    print("HARD")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                else:
                    print('ERROR: Wrong level. Please select a level between 1 and 3')
                    return
                finish_write_file(chosen_params[0])
            except Exception as ex:
                print(ex)
                print("ERROR: Could not create the APT model")
        else:
            print('\nERROR: Invalid option. Please enter either Yes or No.')
    except Exception as e:
        print(e)
        print("\nERROR: Could not create the APT model")


def option2():
    '''
    Esta opción genera un modelo secuencial APT aleatorio orientado a una plataforma específica, con la opción de configurar parámetros aleatorios o no.
    :return: modelo secuencial de un APT aleatorio generado.
    '''
    try:
        print("Let's generate a random APT model\n")
        opt = str(input('Do you want to configure some of the parameters? Yes/No: ')).lower()
        if opt == 'yes':
            try:
                print("\nLet's configure some parameters together :)\n")
                chosen_params = choose_parameters()
                print("How difficult do you want it to be?")
                print("1 - Be kind please (Easy)")
                print("2 - Let's give it a try (Medium)")
                print("3 - Go hard or go home! Show me what you got! (Hard)")
                level = int(input('\nChoose a level of difficulty: '))
                if level == 1:
                    print("EASY")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 2:
                    print("MEDIUM")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 3:
                    print("HARD")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                else:
                    print('ERROR: Wrong level. Please select a level between 1 and 3')
                    return
                finish_write_file(chosen_params[0])
            except Exception as ex:
                print(ex)
                print("ERROR: Could not create the random APT model with those parameters")
        elif opt == 'no':
            try:
                chosen_params = generate_parameters()
                print("\nHow difficult do you want it to be?")
                print("1 - Be kind please (Easy)")
                print("2 - Let's give it a try (Medium)")
                print("3 - Go hard or go home! Show me what you got! (Hard)")
                level = int(input('\nChoose a level of difficulty: '))
                if level == 1:
                    print("EASY")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 2:
                    print("MEDIUM")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                elif level == 3:
                    print("HARD")
                    print("Generating the real APT model, wait a sec...\n")
                    SequentialRandomModel.generate_random_sequential_model(option, chosen_params)
                else:
                    print('ERROR: Wrong level. Please select a level between 1 and 3')
                    return
                finish_write_file(chosen_params[0])
            except Exception as ex:
                print(ex)
                print("ERROR: Could not create the random APT model")
        else:
            print('\nERROR: Invalid option. Please enter either Yes or No.')
    except Exception as e:
        print(e)
        print("\nERROR: Could not create the random APT model")

def option3():
    '''
    :return: abre un enlace en el navegador con la página web de Visualizador de STIX.
    '''
    print("Redirecting to the website")
    webbrowser.open('https://oasis-open.github.io/cti-stix-visualization/')


def option4():
    '''
    Esta opción muestra información sobre el TFM, como el nombre, el director y la universidad.
    :return: String
    '''
    print("\n-----APT MODEL SIMULATOR-----")
    print("This is a Project made by Oscar Jover Walsh in colaboration with Laura Sanz García")
    print("Directed by: Víctor A. Villagrá")
    print("Master Universitario en Ingeniería de Telecomunicaciones - Universidad Politécnica de Madrid\n")


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='A tutorial of APT Model Generator!')
        parser.add_argument("-f", default=1, help="YAML config file")

        args = parser.parse_args()
        filename = args.f
        if filename == 1:
            while True:
                print_menu()
                option = ''
                try:
                    option = int(input('\nPlease, select an option: '))
                except Exception as e:
                    print(e)
                    print('ERROR: Wrong input. Please enter a number ...')
                if option == 1:
                    option1()
                elif option == 2:
                    option2()
                elif option == 3:
                    option3()
                elif option == 4:
                    option4()
                elif option == 5:
                    print('\nGOODBYE HACKER!')
                    exit()
                else:
                    print('Invalid option. Please enter a number between 1 and 5.')
        else:
            try:
                with open('YAMLConfigFile.yaml') as f:
                    data = yaml.load(f, Loader=yaml.FullLoader)

                if data['Model'] == 1:
                    total_params = []
                    apt_name = ''
                    platform = ''
                    objective = ''
                    timer = 60 * data['Timer']
                    level = data['Level']

                    if intrusionSetNameList == []:
                        show_threat_actors()
                    if data['Parameters']:
                        if data['APTGroup']:
                            try:
                                if data['APTGroupName'] in intrusionSetNameList:
                                    apt_name = data['APTGroupName']
                            except Exception as ex:
                                print(ex)
                                print('ERROR: Wrong APT Group. Please, check the APT group list')
                        if not data['APTGroup']:
                            apt_name = random.choice(show_threat_actors())
                        total_params.append(apt_name)

                        platforms = SequentialRandomModel.get_platforms_of_attacks()
                        if data['PlatformName'].lower() in platforms:
                            platform = data['PlatformName'].lower()
                        else:
                            platform = random.choice(SequentialRandomModel.get_platforms_of_attacks())
                        total_params.append(platform)

                        if data['Objective']:
                            objectives = SequentialRandomModel.get_objectives_of_attacks()
                            if 1 <= data['ObjectivePhase'] <= 14:
                                objectiveNum = data['ObjectivePhase'] 
                                objective = objectives[data['ObjectivePhase']]
                        if not data['Objective']:
                            objectives = SequentialRandomModel.get_objectives_of_attacks()
                            objectiveNum = random.randint(1, 14)
                            objective = objectives[objectiveNum]
                        total_params.append(objectiveNum)
                        total_params.append(timer)
                        total_params.append(level)

                    if not data['Parameters']:
                        total_params = generate_parameters()
                    adversary_yaml_file(total_params[0], attackPatternId, total_params[1], timer, total_params[2])
                    finish_write_file(total_params[0])

                if data['Model'] == 2:
                    total_params = []
                    apt_name = ''
                    platform = ''
                    objective = ''
                    timer = 60 * data['Timer']
                    level = data['Level']

                    if data['Parameters']:
                        if data['APTGroup']:
                            apt_name = data['APTGroupName']
                        if not data['APTGroup']:
                            apt_name = random_words_gen.pick_two_random_words()
                        total_params.append(apt_name)

                        platforms = SequentialRandomModel.get_platforms_of_attacks()
                        if data['PlatformName'].lower() in platforms:
                            platform = data['PlatformName'].lower()
                        else:
                            platform = random.choice(SequentialRandomModel.get_platforms_of_attacks())
                        total_params.append(platform)

                        if data['Objective']:
                            objectives = SequentialRandomModel.get_objectives_of_attacks()
                            if 1 <= data['ObjectivePhase'] <= 14:
                                objective = data['ObjectivePhase']
                        if not data['Objective']:
                            objectives = SequentialRandomModel.get_objectives_of_attacks()
                            objective = random.randint(1, 14)
                        total_params.append(objective)
                        
                    if not data['Parameters']:
                        total_params = generate_parameters()
                        platforms = SequentialRandomModel.get_platforms_of_attacks()
                        if data['PlatformName'].lower() in platforms:
                            platform = data['PlatformName'].lower()
                        else:
                            platform = random.choice(SequentialRandomModel.get_platforms_of_attacks())
                        del total_params[1]
                        total_params.insert(1, platform)
                    total_params.append(timer)
                    total_params.append(level)
                    print('The selected parameters are: ', total_params)
                    SequentialRandomModel.generate_random_sequential_model(option, total_params)
                    finish_write_file(total_params[0])
            except Exception as ex:
                print(ex)
                print('ERROR: Wrong YAML configuration file')
    except Exception as e:
        print(e)
        print('ERROR: Wrong input. Execute the option --h to see help')