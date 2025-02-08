# Test Organization

This project's tests are organized into two categories:

## Unit Tests

Located in the `unit/` directory, these tests:
- Do not make external API calls
- Use mocked data
- Run quickly
- Are suitable for CI/CD pipelines
- Run by default with `pytest`

## Integration Tests

Located in the `integration/` directory, these tests:
- Make real API calls
- Test actual integration with external services
- Take longer to run
- Require internet connectivity
- Are marked with `@pytest.mark.integration`
- Are excluded by default

## Running Tests

1. Run only unit tests (default):
```bash
pytest
```

2. Run only integration tests:
```bash
pytest -m integration
```

3. Run all tests:
```bash
pytest -m "integration or not integration"
```

## Test Data

Common test fixtures are located in `conftest.py` and are shared between unit and integration tests. These fixtures provide:
- Sample price data
- Sample portfolio positions
- Sample beta values
- Mock yfinance data
- Sample market data
- Sample exchange rates

## Best Practices

1. Always add new unit tests for new functionality
2. Use mocks for external services in unit tests
3. Add integration tests for critical external service interactions
4. Keep integration tests focused and minimal to reduce API usage
5. Use shared fixtures from conftest.py when possible 