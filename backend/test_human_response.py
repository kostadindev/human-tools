#!/usr/bin/env python3
"""
Test script to simulate a human responding to queries.
Run this while the agent is waiting for a response.
"""
import httpx
import sys

HUMAN_API_URL = "http://localhost:8001"


def get_pending_queries():
    """Get all pending queries"""
    response = httpx.get(f"{HUMAN_API_URL}/pending-queries")
    response.raise_for_status()
    return response.json()


def submit_response(query_id: str, response_text: str):
    """Submit a response to a query"""
    response = httpx.post(
        f"{HUMAN_API_URL}/respond/{query_id}",
        json={"response": response_text}
    )
    response.raise_for_status()
    return response.json()


def main():
    print("\n" + "="*60)
    print("🧑 HUMAN RESPONSE SIMULATOR")
    print("="*60)

    # Get pending queries
    pending = get_pending_queries()

    if not pending:
        print("\n❌ No pending queries found.")
        print("\nMake sure:")
        print("  1. Human API is running (python human_api.py)")
        print("  2. Agent has asked a question that triggers query_human tool")
        return

    print(f"\n📋 Found {len(pending)} pending queries:\n")

    # Show all pending queries
    for i, query in enumerate(pending, 1):
        print(f"{i}. [{query['query_id'][:8]}...] {query['question']}")

    # Ask user to select one
    print()
    try:
        choice = int(input(f"Select query to answer (1-{len(pending)}): "))
        if choice < 1 or choice > len(pending):
            print("❌ Invalid choice")
            return

        selected_query = pending[choice - 1]
        print(f"\n📝 Question: {selected_query['question']}")
        response_text = input("💬 Your response: ")

        if not response_text.strip():
            print("❌ Response cannot be empty")
            return

        # Submit response
        result = submit_response(selected_query['query_id'], response_text)
        print(f"\n✅ {result['message']}")
        print("The agent should receive your response within 10 seconds!\n")

    except ValueError:
        print("❌ Invalid input")
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
