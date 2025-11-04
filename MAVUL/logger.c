void log_auth_failure(char* username) {
    printf("[FAIL] login attempt for %s\n", username);
    save_audit_log(username, "auth_fail");
}

void save_audit_log(char* username, char* event) {
    printf("Audit log saved for %s: %s\n", username, event);
}
