{
    "openapi": "3.1.0",
    "info": {
        "title": "FastAPI",
        "version": "0.1.0"
    },
    "paths": {
        "/": {
            "get": {
                "summary": "Read Root",
                "operationId": "read_root__get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {}
                            }
                        }
                    }
                }
            }
        },
        "/favicon.ico": {
            "get": {
                "summary": "Favicon",
                "operationId": "favicon_favicon_ico_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {}
                            }
                        }
                    }
                }
            }
        },
        "/queries": {
            "get": {
                "summary": "List Querys",
                "description": "scan all response items to create a list of all unique query values",
                "operationId": "list_querys_queries_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "items": {
                                        "type": "object"
                                    },
                                    "type": "array",
                                    "title": "Response List Querys Queries Get"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/responses/{query}": {
            "get": {
                "summary": "List Responses",
                "description": "return a list of responses from requests with query",
                "operationId": "list_responses_responses__query__get",
                "parameters": [
                    {
                        "name": "query",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "title": "Query"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object"
                                    },
                                    "title": "Response List Responses Responses  Query  Get"
                                }
                            }
                        }
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/snippets/{response_id}": {
            "get": {
                "summary": "List Snippets",
                "description": "return the list of snipped associated with the given response_id",
                "operationId": "list_snippets_snippets__response_id__get",
                "parameters": [
                    {
                        "name": "response_id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "string",
                            "title": "Response Id"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object"
                                    },
                                    "title": "Response List Snippets Snippets  Response Id  Get"
                                }
                            }
                        }
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "HTTPValidationError": {
                "properties": {
                    "detail": {
                        "items": {
                            "$ref": "#/components/schemas/ValidationError"
                        },
                        "type": "array",
                        "title": "Detail"
                    }
                },
                "type": "object",
                "title": "HTTPValidationError"
            },
            "ValidationError": {
                "properties": {
                    "loc": {
                        "items": {
                            "anyOf": [
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "integer"
                                }
                            ]
                        },
                        "type": "array",
                        "title": "Location"
                    },
                    "msg": {
                        "type": "string",
                        "title": "Message"
                    },
                    "type": {
                        "type": "string",
                        "title": "Error Type"
                    }
                },
                "type": "object",
                "required": [
                    "loc",
                    "msg",
                    "type"
                ],
                "title": "ValidationError"
            }
        }
    }
}