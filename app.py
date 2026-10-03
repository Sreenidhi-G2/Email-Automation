from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

HUNTER_API_URL = "https://api.hunter.io/v2/domain-search"


@app.route("/process", methods=["POST"])
def process_domain():
    try:
        # Get domain from Make
        data = request.get_json()

        if not data or "domain" not in data:
            return jsonify({
                "status": "failed",
                "error": "Missing domain"
            }), 400

        domain = data["domain"].strip()

        if not domain:
            return jsonify({
                "status": "failed",
                "error": "Domain cannot be empty"
            }), 400

        # Get Hunter API key from environment variable
        api_key = os.getenv("HUNTER_API_KEY")
        if not api_key:
            return jsonify({
                "status": "failed",
                "error": "HUNTER_API_KEY is not configured"
            }), 500

        # Call Hunter
        response = requests.get(
            HUNTER_API_URL,
            params={
                "domain": domain,
                "department": "hr",
                "api_key": api_key
            },
            timeout=30
        )

        # Hunter returned an error
        if response.status_code != 200:
            return jsonify({
                "status": "failed",
                "domain": domain,
                "error": "Hunter API request failed",
                "hunter_status": response.status_code,
                "hunter_response": response.json()
            }), 502

        hunter_data = response.json()
        data = hunter_data.get("data", {})

        emails = data.get("emails", [])

        # Extract only the fields we need
        people = []

        for person in emails:
            people.append({
                "email": person.get("value"),
                "first_name": person.get("first_name"),
                "last_name": person.get("last_name"),
                "position": person.get("position"),
                "seniority": person.get("seniority"),
                "department": person.get("department")
            })

        return jsonify({
            "status": "success",
            "domain": domain,
            "count": len(people),
            "people": people
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "failed",
            "error": "Hunter API request timed out"
        }), 504

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 502

    except Exception as e:
        return jsonify({
            "status": "failed",
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )