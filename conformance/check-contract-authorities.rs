#![forbid(unsafe_code)]
use std::{fs, process::ExitCode};

fn main() -> ExitCode {
    let tsp = fs::read_to_string("contracts/typespec/engineering-ops-boundaries.tsp").unwrap_or_default();
    let boundary_schema = fs::read_to_string("schemas/boundaries.schema.json").unwrap_or_default();
    let mut errors = Vec::new();

    for field in [
        "github", "linear", "slack", "apps", "owners", "logins", "secondaryLogins",
        "userEmail", "workspaceName", "workspaceUrl", "mcpUrl", "domain", "teamId",
    ] {
        if !tsp.contains(field) || !boundary_schema.contains(&format!("\"{field}\"")) {
            errors.push(format!("TypeSpec/JSON Schema boundary drift: {field}"));
        }
    }

    for schema_path in [
        "schemas/app.schema.json",
        "schemas/boundaries.schema.json",
        "schemas/marketplace.schema.json",
        "schemas/mcp.schema.json",
        "schemas/plugin.schema.json",
    ] {
        let schema = fs::read_to_string(schema_path).unwrap_or_default();
        if !schema.contains("https://json-schema.org/draft/2020-12/schema") {
            errors.push(format!("{schema_path} is not Draft 2020-12"));
        }
    }

    if !boundary_schema.contains("\"required\": [\"github\", \"linear\", \"slack\", \"apps\"]") {
        errors.push("top-level account/app boundary requirements drifted".into());
    }
    if !tsp.contains("model EngineeringOpsBoundaries") {
        errors.push("TypeSpec boundary authority is incomplete".into());
    }

    if errors.is_empty() {
        ExitCode::SUCCESS
    } else {
        for error in errors { eprintln!("conformance error: {error}"); }
        ExitCode::FAILURE
    }
}
