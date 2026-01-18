"""JSON schema for Gemini evaluation response."""


def get_evaluation_response_schema() -> dict:
    """
    Get the JSON schema for Gemini evaluation response.

    Returns:
        JSON schema dictionary for structured output
    """
    return {
        "type": "object",
        "properties": {
            "overallVerdict": {
                "type": "string",
                "enum": ["pass", "fail", "needs_review"],
            },
            "overallVerdictReason": {
                "type": "string",
                "description": "Detailed reasoning for the overall verdict based on claim evaluations, authenticity analysis, and visual analysis",
            },
            "confidenceScore": {"type": "integer"},
            "riskLevel": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
            },
            "classification": {
                "type": "object",
                "properties": {
                    "detectedType": {
                        "type": "string",
                        "enum": ["CERTIFICATION", "INVOICE", "LICENSE", "UNKNOWN"],
                    },
                    "typeConfidence": {
                        "type": "integer",
                    },
                    "detectedLanguage": {"type": "string"},
                    "detectedCountry": {"type": "string"},
                    "detectedIssuer": {"type": "string"},
                    "documentCategory": {
                        "type": "string",
                        "enum": [
                            "ENVIRONMENT",
                            "SUSTAINABILITY",
                            "SOCIAL",
                            "GOVERNANCE",
                            "TRACEABILITY",
                            "OTHER",
                        ],
                    },
                },
                "required": [
                    "detectedType",
                    "typeConfidence",
                ],
            },
            "claimEvaluations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claimId": {
                            "type": "string",
                            "description": "Must match the 'id' from input claims (as string)",
                        },
                        "claimName": {"type": "string"},
                        "result": {
                            "type": "string",
                            "enum": ["PASS", "FAIL"],
                            "description": "PASS if claim is satisfied, FAIL if not",
                        },
                        "confidence": {
                            "type": "integer",
                            "description": "Confidence score (0-100) for this claim evaluation",
                        },
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "reasoning": {"type": "string"},
                        "issues": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "claimId",
                        "claimName",
                        "result",
                        "confidence",
                        "evidence",
                        "reasoning",
                        "issues",
                    ],
                },
            },
            "authenticityAnalysis": {
                "type": "object",
                "properties": {
                    "authenticityScore": {
                        "type": "integer",
                    },
                    "securityElements": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["authenticityScore", "securityElements"],
            },
            "extractedContent": {
                "type": "object",
                "properties": {
                    "documentTitle": {"type": "string"},
                    "documentNumber": {"type": "string"},
                    "issueDate": {"type": "string"},
                    "expirationDate": {"type": "string"},
                    "issuingOrganization": {"type": "string"},
                    "certifiedProducts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "certifiedProducts",
                    "materials",
                ],
            },
            "visualAnalysis": {
                "type": "object",
                "properties": {
                    "pageCount": {
                        "type": "integer",
                    },
                    "orientation": {
                        "type": "string",
                        "enum": ["portrait", "landscape", "mixed", "unknown"],
                    },
                    "overallQuality": {
                        "type": "string",
                        "enum": ["good", "fair", "poor", "unknown"],
                    },
                },
                "required": ["pageCount", "orientation", "overallQuality"],
            },
            "issuerAnalysis": {
                "type": "object",
                "properties": {
                    "issuerName": {"type": "string"},
                    "issuerType": {"type": "string"},
                    "issuerCountry": {"type": "string"},
                    "issuerAccreditationNumber": {"type": "string"},
                    "issuerScope": {"type": "string"},
                    "issuerContact": {"type": "string"},
                    "issuerValidity": {"type": "string"},
                    "issuerVerificationStatus": {"type": "string"},
                    "issues": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["issues"],
            },
            "jurisdictionAnalysis": {
                "type": "object",
                "properties": {
                    "jurisdiction": {"type": "string"},
                    "confidence": {
                        "type": "integer",
                    },
                    "issues": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["issues"],
            },
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                    "required": ["title", "detail"],
                },
            },
        },
        "required": [
            "overallVerdict",
            "overallVerdictReason",
            "confidenceScore",
            "riskLevel",
            "classification",
            "claimEvaluations",
            "authenticityAnalysis",
            "extractedContent",
            "visualAnalysis",
            "issuerAnalysis",
            "jurisdictionAnalysis",
            "recommendations",
        ],
    }
