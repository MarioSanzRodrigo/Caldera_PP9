import sqlite3
import main
from datetime import datetime
import os
import yaml
import uuid
import math
import random
import random_words_gen

#########################################################################################

directory = os.getcwd()
directory = directory.replace("\\", "/")
db_file = directory + '/COBRA_ddbb.sqlite' # path to the local db file
conn = None

try:
    conn = sqlite3.connect(db_file)
except Error as e:
    print(e)
    

def generate_random_sequential_model(option, chosen_params):
    '''
    Esta función realiza las llamadas a las distintas funciones para generar el modelo secuencial de un grupo APT aleatorio.
    :param: level: Nivel de complejidad del modelo elegido por el usuario.
    :param: apt_name: Nombre del grupo APT existente elegido por el usuario.
    '''
    print("Generating APT model")
    get_tactic_phase_names(chosen_params[0], chosen_params[1], chosen_params[2], chosen_params[3], chosen_params[4])
    if option == 2:
        get_platforms_of_attacks()


def get_tactic_phase_names(apt_name, platform, objective, timer, level):
    '''
    Esta función extrae de la BBDD las etapas que componen el modelo.
    :param: level: Nivel de complejidad del modelo elegido por el usuario.
    :return: tactics: array con los nombres y número de las etapas que coomponen el modelo.
    '''
    if objective > 1:
        objective = objective - 1
    tacticsCur = conn.cursor()
    tacticsCur.execute("SELECT DISTINCT phase_number, phase_name FROM kill_chain_phases INNER JOIN sdos_object ON sdos_object.id = kill_chain_phases.fk_object_id WHERE x_mitre_platforms_" + platform + " LIKE '%true%' GROUP BY fk_object_id ORDER BY phase_number LIMIT ?", (objective,))
    main.tactics = tacticsCur.fetchall()
    for row in main.tactics:
        main.tacticNumber.append(row[0])
        main.tacticNames.append(row[1])
    main.tactics.sort()
    if objective > 0:
        objective = objective + 1
    get_level_model(level, objective)
    find_attack_patterns_data_sources_platforms(platform, apt_name, objective, timer)
    return main.tactics


def get_level_model(level, objective):
    i = len(main.tacticNumber)
    if objective != 1:
        if level == 1:
            i = (i-1)/3
        elif level == 2:
            i = ((i-1)/3)*2
        elif level == 3:
            i = i-1
    n = 0
    a = main.tacticNumber.pop()
    main.attackList = random.sample(main.tacticNumber, math.floor(i))
    main.attackList.append(a)
    main.attackList.sort()
    main.tacticNumber = main.attackList
    print('APT phases:', main.tacticNumber)
    return main.attackList


def get_platforms_of_attacks():
    '''
    Esta función devuelve un listado con todas las plataformas posibles a elegir por el usuario.
    Versión completa: platforms = ['windows', 'macos', 'office_365', 'linux', 'azure_ad', 'azure', 'gcp', 'aws', 'saas', 'android']
    :return: platforms: lista con las plataformas presentes.
    '''
    platforms = ['windows', 'linux']
    return platforms


def get_objectives_of_attacks():
    '''
    Esta función devuelve un listado con todas las etapas del la caden CKCM a elegir por el usuario.
    :return: platforms: lista con las etapas presentes.
    '''
    objectives = {3: 'Initial Access', 4: 'Execution', 5: 'Persistence', 6: 'Privilege Escalation', 7: 'Defense Evasion', 8: 'Credential Access', 9: 'Discovery', 10: 'Lateral Movement', 11: 'Collection', 12: 'Command and Control', 13: 'Exfiltration', 14: 'Impact'}
    return objectives


def find_attack_patterns_data_sources_platforms(platform, apt_name, objective, timer):
    '''
    Esta función extrae los atributos correspondientes a los distintos objetos attack-pattern del modelo. Dichos objetos se almacenarán en el fichero .json.
    :param: platform: plataforma elegida por el usuario o elegida aleatoriamente.
    :param: apt_name: Nombre del grupo APT existente elegido por el usuario o elegida aleatoriamente.
    :return: devuelve una lista con los IDs de los objetos STIX (SDO) del tipo attack-pattern.
    '''
    for phase in main.tacticNumber:
        attackPatternCur = conn.cursor()
        attackPatternCur.execute("SELECT type, kcp.fk_object_id, phase_name, phase_number FROM sdos_object INNER JOIN kill_chain_phases kcp on sdos_object.id = kcp.fk_object_id WHERE x_mitre_platforms_" + platform + " LIKE '%true%' AND phase_number = ? ORDER BY RANDOM() LIMIT 1", (phase,))
        attackPatterns = attackPatternCur.fetchall()
        for row in attackPatterns:
            main.attackPatternTypes.append(row[0])
            main.attackPatternId.append(row[1])
            main.attackPatternPhaseNames.append(row[2])
            main.attackPatternPhaseNumber.append(row[3])

    print('Model phases:', main.attackPatternPhaseNames)
    main.adversary_yaml_file(apt_name, main.attackPatternId, platform, timer, objective)
    return main.attackPatternId