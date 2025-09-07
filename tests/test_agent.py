from cyberzard.agent import run_agent

def test_agent_degraded_mode():
    result = run_agent(provider="openai", user_query="Say hi", max_steps=1)
    assert "final" in result
    assert isinstance(result["final"], str)
