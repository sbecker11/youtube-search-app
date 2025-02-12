


def save_openapi_docs(self, url, output_path='./docs/openapi.json'):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    spec = response.json()

    # Validate the OpenAPI spec
    validate_spec(spec)

    # Save the JSON to file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(spec, file, indent=2)

    print(f"OpenAPI spec saved to {output_path}")

