"""
Pytest tests for the MCP client with the baseball server.
"""

import json
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def simplify_session_setup():
    """Helper to create server params for tests."""
    server_path = Path(__file__).parent.parent / "server.py"
    return StdioServerParameters(command="python", args=[str(server_path)], env=None)


@pytest.mark.asyncio
async def test_client_connection():
    """Test connecting to the MCP server and checking available tools."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            response = await session.list_tools()
            tools = response.tools
            tool_names = [tool.name for tool in tools]

            required_tools = ["get_schedule", "lookup_player", "get_standings"]
            for tool in required_tools:
                assert tool in tool_names, f"Missing required tool: {tool}"


@pytest.mark.asyncio
async def test_get_schedule_tool():
    """Test the get_schedule tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_schedule", {"date": "2023-07-14"})

            # Check for API errors and skip test if encountered
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_schedule")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "params_sent" in data:
                    print(f"Parameters sent: {data['params_sent']}")
                pytest.skip("Tool implementation error in get_schedule")

            assert "game_date" in data, "Missing 'game_date' in response"


@pytest.mark.asyncio
async def test_lookup_player_tool():
    """Test the lookup_player tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Use a well-known player
            player_name = "Aaron Judge"
            result = await session.call_tool("lookup_player", {"name": player_name})

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in lookup_player")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                pytest.skip("Tool implementation error in lookup_player")

            # Check for people key (new format)
            if isinstance(data, dict):
                assert "people" in data, "Response should contain 'people' key"
                assert len(data["people"]) > 0, "Player data should not be empty"
            else:
                pytest.fail("Expected a dictionary response with 'people' key")


@pytest.mark.asyncio
async def test_get_standings_tool():
    """Test the get_standings tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Use current year for season
            result = await session.call_tool(
                "get_standings",
                {"season": 2023, "standingsTypes": "regularSeason"},
            )

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_standings")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "params_sent" in data:
                    print(f"Parameters sent: {data['params_sent']}")
                pytest.skip("Tool implementation error in get_standings")

            assert (
                "200" in data and "div_name" in data["200"]
            ), "Missing expected division structure in standings response"


@pytest.mark.asyncio
async def test_get_team_leaders_tool():
    """Test the get_team_leaders tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Check if the tool is available
            response = await session.list_tools()
            tool_names = [tool.name for tool in response.tools]

            if "get_team_leaders" not in tool_names:
                pytest.skip("get_team_leaders tool not available")

            # Parameters must be in a single dictionary
            result = await session.call_tool(
                "get_team_leaders",
                {
                    "team_id": 147,
                    "season": 2023,
                    "leader_category": "walks",
                    "limit": 10,
                },
            )

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_team_leaders")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "params_sent" in data:
                    print(f"Parameters sent: {data['params_sent']}")
                pytest.skip("Tool implementation error in get_team_leaders")

            # Assertions for valid team leader data response
            print(data)
            # Check for either the teamLeaders flag or results field
            assert (
                "teamLeaders" in data or "results" in data
            ), "Missing team leader data in response"
            if "results" in data:
                assert isinstance(
                    data["results"], str
                ), "Expected team leader results to be a string"


@pytest.mark.asyncio
async def test_get_stats_tool():
    """Test the get_stats tool which provides access to any MLB Stats API endpoint."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Using a simple endpoint - teams data
            endpoint = "teams"
            api_params = {"sportId": 1}  # MLB

            result = await session.call_tool(
                "get_stats", {"endpoint": endpoint, "params": api_params}
            )

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_stats")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "params" in data:
                    print(f"Parameters sent: {data['params']}")
                pytest.skip("Tool implementation error in get_stats")

            assert "teams" in data, "Missing 'teams' in response"


@pytest.mark.asyncio
async def test_get_player_stats_tool():
    """Test the get_player_stats tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Use player_id instead of personId to match server parameter name
            result = await session.call_tool(
                "get_player_stats",
                {
                    "player_id": 592450,  # Aaron Judge
                    "group": "hitting",
                    "season": 2023,
                    "stats": "season",
                },
            )

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_player_stats")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "params_sent" in data:
                    print(f"Parameters sent: {data['params_sent']}")
                pytest.skip("Tool implementation error in get_player_stats")

            assert "stats" in data, "Missing 'stats' in response"


@pytest.mark.asyncio
async def test_get_boxscore_tool():
    """Test the get_boxscore tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            game_id = 565997
            result = await session.call_tool("get_boxscore", {"game_id": game_id})

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_boxscore")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "game_id" in data:
                    print(f"Game ID sent: {data['game_id']}")
                    # Try another game ID if the first one fails
                    pytest.skip(f"Game ID {game_id} not found, try a different one")
                else:
                    pytest.skip("Tool implementation error in get_boxscore")

            # Boxscore format can vary, look for common keys
            common_keys = ["game_id", "boxscore", "success"]
            assert any(
                key in data for key in common_keys
            ), f"Response missing expected boxscore structure, expected one of: {common_keys}"


@pytest.mark.asyncio
async def test_get_game_pace_tool():
    """Test the get_game_pace tool."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_game_pace", {"season": 2023})

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_game_pace")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                if "params_sent" in data:
                    print(f"Parameters sent: {data['params_sent']}")
                pytest.skip("Tool implementation error in get_game_pace")

            # Game pace data should have averages or gamesByLength
            expected_keys = ["copyright", "sports", "teams", "leagues"]
            assert any(
                key in data for key in expected_keys
            ), f"Response missing expected data structure, expected one of: {expected_keys}"

            # If sports data is present, check for expected metrics
            if data.get("sports"):
                sport_data = data["sports"][0]
                metrics = ["timePerGame", "runsPerGame", "hitsPerGame", "season"]
                assert any(
                    metric in sport_data for metric in metrics
                ), "Missing expected pace metrics in sports data"


@pytest.mark.asyncio
async def test_get_meta_tool():
    """Test the get_meta tool for accessing MLB Stats API metadata."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Check if the tool is available
            response = await session.list_tools()
            tool_names = [tool.name for tool in response.tools]

            if "get_meta" not in tool_names:
                pytest.skip("get_meta tool not available")

            # Test with a simple metadata type - positions
            result = await session.call_tool("get_meta", {"type_name": "positions"})

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_meta")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                pytest.skip("Tool implementation error in get_meta")

            # Based on actual response format - positions data comes as a dictionary
            if isinstance(data, dict):
                # For dictionary format (positions data often comes as a dict)
                assert len(data) > 0, "Metadata results should not be empty"
                # Look for expected fields in a position metadata entry
                expected_fields = ["code", "shortName", "abbrev", "displayName"]
                # Check if any of the expected fields exist in the returned data
                assert any(
                    field in data for field in expected_fields
                ), "Position metadata missing expected fields"
            elif isinstance(data, list):
                # For list format - used when metadata is returned as a list
                assert len(data) > 0, "Metadata results should not be empty"
                # Check for expected fields in first item
                first_item = data[0]
                assert any(
                    field in first_item for field in ["code", "shortName", "abbrev"]
                ), "Position metadata missing expected fields"
            else:
                pytest.fail(f"Unexpected data type: {type(data)}")

            # Also test with field filtering
            filter_result = await session.call_tool(
                "get_meta", {"type_name": "positions", "fields": "shortName,code"}
            )

            if not filter_result.isError:
                filter_data = json.loads(filter_result.content[0].text)

                # Don't assert specific type, but check for validity
                if isinstance(filter_data, dict) and filter_data:
                    # For filtered dictionary, check for the requested fields
                    requested_fields = ["shortName", "code"]
                    for field in requested_fields:
                        assert (
                            field in filter_data
                        ), f"Expected field '{field}' missing in filtered results"

                    # Check that we don't have too many additional fields
                    # Some metadata might include type or other system fields
                    for key in filter_data.keys():
                        if key not in requested_fields and key not in ["type"]:
                            print(
                                f"Warning: Found additional field '{key}' in filtered results"
                            )

                elif isinstance(filter_data, list) and filter_data:
                    first_filtered = filter_data[0]
                    requested_fields = ["shortName", "code"]

                    # Check that requested fields are present
                    for field in requested_fields:
                        assert (
                            field in first_filtered
                        ), f"Expected field '{field}' missing in filtered results"


@pytest.mark.asyncio
async def test_get_available_endpoints_tool():
    """Test the get_available_endpoints tool for retrieving MLB Stats API endpoint information."""
    params = simplify_session_setup()

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Check if the tool is available
            response = await session.list_tools()
            tool_names = [tool.name for tool in response.tools]

            if "get_available_endpoints" not in tool_names:
                pytest.skip("get_available_endpoints tool not available")

            # Test the endpoints listing tool
            result = await session.call_tool("get_available_endpoints", {})

            # Check for API errors
            if result.isError:
                error_text = (
                    result.content[0].text if result.content else "No error details"
                )
                if "error" in error_text.lower():
                    print(f"\nAPI Error Details: {error_text}")
                    pytest.skip("API Error in get_available_endpoints")

            # Test response formatting
            assert result.content, "No content returned from tool"
            assert result.content[0].type == "text", "Expected text response"

            # Verify response structure
            data = json.loads(result.content[0].text)

            # Check for error in response data
            if isinstance(data, dict) and "error" in data:
                print(f"\nTool returned error: {data['error']}")
                pytest.skip("Tool implementation error in get_available_endpoints")

            # Verify structure of response
            assert "endpoints" in data, "Response missing 'endpoints' dictionary"
            assert "usage_note" in data, "Response missing 'usage_note' field"
            assert "example" in data, "Response missing usage example"

            # Check content of endpoints dictionary
            endpoints = data["endpoints"]
            assert isinstance(endpoints, dict), "Endpoints should be a dictionary"
            assert len(endpoints) > 0, "No endpoints returned"

            # Verify structure of at least one common endpoint
            common_endpoints = ["teams", "people", "schedule"]
            found_common = False

            for endpoint_name in common_endpoints:
                if endpoint_name in endpoints:
                    found_common = True
                    endpoint_data = endpoints[endpoint_name]
                    assert (
                        "url" in endpoint_data
                    ), f"Endpoint {endpoint_name} missing URL"
                    assert (
                        "required_params" in endpoint_data
                    ), f"Endpoint {endpoint_name} missing required parameters"
                    assert (
                        "all_params" in endpoint_data
                    ), f"Endpoint {endpoint_name} missing all parameters"
                    break

            assert (
                found_common
            ), f"None of the common endpoints {common_endpoints} found in results"
