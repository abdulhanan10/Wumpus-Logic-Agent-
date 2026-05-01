"""
Flask Web Application — Dynamic Wumpus Logic Agent
AI 2002 Assignment 6 — Question 6
"""

from flask import Flask, jsonify, request, render_template, session
import uuid
import json

from wumpus_world import WumpusWorld, Agent

app = Flask(__name__)
app.secret_key = "wumpus-logic-agent-2026"

# In-memory game sessions
GAMES = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/new_game", methods=["POST"])
def new_game():
    data = request.get_json()
    rows = max(3, min(7, int(data.get("rows", 4))))
    cols = max(3, min(7, int(data.get("cols", 4))))

    game_id = str(uuid.uuid4())
    world = WumpusWorld(rows, cols)
    agent = Agent(rows, cols)

    GAMES[game_id] = {"world": world, "agent": agent}

    state = agent._state(world)
    state["game_id"] = game_id
    return jsonify(state)


@app.route("/api/step", methods=["POST"])
def step():
    data = request.get_json()
    game_id = data.get("game_id")

    if game_id not in GAMES:
        return jsonify({"error": "Game not found"}), 404

    game = GAMES[game_id]
    world = game["world"]
    agent = game["agent"]

    state = agent.step(world)
    state["game_id"] = game_id
    return jsonify(state)


@app.route("/api/reveal", methods=["POST"])
def reveal():
    data = request.get_json()
    game_id = data.get("game_id")

    if game_id not in GAMES:
        return jsonify({"error": "Game not found"}), 404

    game = GAMES[game_id]
    state = game["agent"]._state(game["world"], reveal=True)
    state["game_id"] = game_id
    return jsonify(state)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
