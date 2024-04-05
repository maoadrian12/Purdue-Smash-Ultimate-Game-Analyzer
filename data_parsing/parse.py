import requests
import psycopg2
import json
import time
import re

from environ import API_KEY
from environ import DB_PASS

conn = psycopg2.connect(database="smash_statistics",
                        host="localhost",
                        user="postgres",
                        password=DB_PASS,
                        port="9292")
cursor = conn.cursor()
cursor.execute("SELECT * FROM player WHERE tag = 'AVeryBigNoob'")
print(cursor.fetchall())

URL = "https://api.start.gg/gql/alpha"
headers = {
    "Authorization": "Bearer " + API_KEY
}

def get_tournies():
    body = f'''
        {{
            "query": "query TourneyQuery {{tournaments(query: {{page:1 perPage:300 sortBy:null filter:{{ownerId:1178972}}}}) {{nodes {{ slug}}}}}}",
                "variables": {{}}
        }}
    '''
    r = requests.post(url=URL, data=body, headers=headers)
    output = r.text
    parsed_data = json.loads(output)
    for tourney in parsed_data['data']['tournaments']['nodes']:
        print(tourney['slug'])
        cursor.execute("INSERT INTO tournaments (slug) VALUES (%s) ON CONFLICT DO NOTHING;", (tourney['slug'],))
        conn.commit()

def parse_tournies():
    cursor.execute("SELECT slug FROM tournaments")
    slugs = cursor.fetchall()
    for slug in slugs:
        print(slug[0])
        eventSlug = slug[0] + "/event/ultimate-singles"
        print(eventSlug)
        body = f'''
            {{
                "query": "query TournamentQuery($tourneySlug: String!, $eventSlug: String!) {{tournament(slug: $tourneySlug){{id name events (filter: {{ slug: $eventSlug }}) {{id name sets ( page: 1 perPage: 100) {{ nodes {{ round winnerId displayScore slots {{ entrant {{ name id participants {{ player {{ id }} }} }} }} }} }} }} }} }}",
                "variables": {{"tourneySlug": "{slug[0]}", "eventSlug": "{eventSlug}"}}
            }}
        '''
        r = requests.post(url=URL, data=body, headers=headers)
        output = r.text
        print("output is: " + output)
        parsed_data = json.loads(output)
        try:
            for event in parsed_data['data']['tournament']['events']:
                for game in event['sets']['nodes']:
                    round = game['round']
                    winner_id = game['winnerId']
                    entrant1_id = game['slots'][0]['entrant']['id']
                    entrant1_name = game['slots'][0]['entrant']['name']
                    player1_id = game['slots'][0]['entrant']['participants'][0]['player']['id']
                    print(f"Player 1 entrant ID: {entrant1_id} Player 1 Name: {entrant1_name} Player 1 ID: {player1_id}")
                    entrant2_id = game['slots'][1]['entrant']['id']
                    entrant2_name = game['slots'][1]['entrant']['name']
                    player2_id = game['slots'][1]['entrant']['participants'][0]['player']['id']
                    print(f"Player 2 entrant ID: {entrant2_id} Player 2 Name: {entrant2_name} Player 2 ID: {player2_id}")
                    winnerid = player1_id if winner_id == entrant1_id else player2_id
                    print(f"Winner ID: {winnerid}")
                    loserid = player2_id if winner_id == entrant1_id else player1_id
                    print(f"Loser ID: {loserid}")
                    print(f"roundL: {round}")
                    end_score = game['displayScore']
                    print(f"end score: {end_score}")
                    print()
                    
                    if end_score != "DQ":
                        scores = re.findall(r"\b\d+\b", end_score)
                        score1 = scores[-2]
                        score2 = scores[-1]
                        #parts = end_score.split('-')
                        #score1 = parts[0].split()[-1]
                        #score2 = parts[1].split()[-1]
                        win1 = score1 if score1 > score2 else score2
                        lose1 = score1 if score1 < score2 else score2
                        print(f"winner: {win1} loser: {lose1}")
                        cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player1_id, entrant1_name))
                        cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player2_id, entrant2_name))
                        cursor.execute("INSERT INTO sets2 (winnerid, loserid, tourney_slug, round, winnerscore, loserscore) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;", (winnerid, loserid, eventSlug, round, win1, lose1))
                        conn.commit()
                        
        except Exception:
            print(Exception)
        time.sleep(3)

def parse_tourney(tourneySlug):
    body = f'''
        {{
            "query": "query TournamentQuery($tourneySlug: String!) {{tournament(slug: $tourneySlug){{id name events {{id name sets ( page: 1 perPage: 100) {{ nodes {{ round winnerId slots {{ entrant {{ name id participants {{ player {{ id }} }} }} }} }} }} }} }} }}",
            "variables": {{"tourneySlug": "{tourneySlug}"}}
        }}
    '''
    
    r = requests.post(url=URL, data=body, headers=headers)
    output = r.text
    parsed_data = json.loads(output)
    for event in parsed_data['data']['tournament']['events']:
        for game in event['sets']['nodes']:
            round = game['round']
            winner_id = game['winnerId']
            entrant1_id = game['slots'][0]['entrant']['id']
            entrant1_name = game['slots'][0]['entrant']['name']
            player1_id = game['slots'][0]['entrant']['participants'][0]['player']['id']
            print(f"Player 1 entrant ID: {entrant1_id} Player 1 Name: {entrant1_name} Player 1 ID: {player1_id}")
            entrant2_id = game['slots'][1]['entrant']['id']
            entrant2_name = game['slots'][1]['entrant']['name']
            player2_id = game['slots'][1]['entrant']['participants'][0]['player']['id']
            print(f"Player 2 entrant ID: {entrant2_id} Player 2 Name: {entrant2_name} Player 2 ID: {player2_id}")
            winnerid = player1_id if winner_id == entrant1_id else player2_id
            print(f"Winner ID: {winnerid}")
            loserid = player2_id if winner_id == entrant1_id else player1_id
            print(f"Loser ID: {loserid}")
            print(f"roundL: {round}")
            #cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player1_id, entrant1_name))
            #cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player2_id, entrant2_name))
            cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player1_id, entrant1_name))
            cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player2_id, entrant2_name))
            cursor.execute("INSERT INTO sets (winnerid, loserid, round) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", (winnerid, loserid, round))
            conn.commit()
            print()

def parse_all_tourneys():
    for i in range(2, 8):
        tourneySlug = f"tournament/boiling-point-{i}"
        body = f'''
            {{
                "query": "query TournamentQuery($tourneySlug: String!) {{tournament(slug: $tourneySlug){{id name events {{id name sets ( page: 1 perPage: 100) {{ nodes {{ round winnerId slots {{ entrant {{ name id participants {{ player {{ id }} }} }} }} }} }} }} }} }}",
                "variables": {{"tourneySlug": "{tourneySlug}"}}
            }}
        '''

        r = requests.post(url=URL, data=body, headers=headers)

        output = r.text
        parsed_data = json.loads(output)
        for event in parsed_data['data']['tournament']['events']:
            for game in event['sets']['nodes']:
                round = game['round']
                winner_id = game['winnerId']
                entrant1_id = game['slots'][0]['entrant']['id']
                entrant1_name = game['slots'][0]['entrant']['name']
                player1_id = game['slots'][0]['entrant']['participants'][0]['player']['id']
                print(f"Player 1 entrant ID: {entrant1_id} Player 1 Name: {entrant1_name} Player 1 ID: {player1_id}")
                entrant2_id = game['slots'][1]['entrant']['id']
                entrant2_name = game['slots'][1]['entrant']['name']
                player2_id = game['slots'][1]['entrant']['participants'][0]['player']['id']
                print(f"Player 2 entrant ID: {entrant2_id} Player 2 Name: {entrant2_name} Player 2 ID: {player2_id}")
                winnerid = player1_id if winner_id == entrant1_id else player2_id
                print(f"Winner ID: {winnerid}")
                loserid = player2_id if winner_id == entrant1_id else player1_id
                print(f"Loser ID: {loserid}")
                print(f"roundL: {round}")
                #cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player1_id, entrant1_name))
                #cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;", (player2_id, entrant2_name))
                cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET tag = EXCLUDED.tag;", (player1_id, entrant1_name))
                cursor.execute("INSERT INTO player (id, tag) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET tag = EXCLUDED.tag;", (player2_id, entrant2_name))
                cursor.execute("INSERT INTO sets (winnerid, loserid, round) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", (winnerid, loserid, round))
                conn.commit()
                print()


choice = input("Would you like to parse a single tourney or all tourneys? (single/all/tournies/parse) ")
if choice == "all":
    parse_all_tourneys()
elif choice == "single":
    tourneySlug = input("Enter the tourney slug: ")
    parse_tourney(tourneySlug)
elif choice == "tournies":
    get_tournies()
elif choice == "parse":
    parse_tournies()
else:
    print("Invalid input")