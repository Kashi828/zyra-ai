package com.zyra.session

/**
 * Test/development implementation only.
 * Replace with Android Keystore-backed encrypted storage in the app build.
 */
class InMemorySecureSessionStorage : SecureSessionStorage {
    private var state: PersistedSessionState? = null

    override fun save(state: PersistedSessionState) {
        this.state = state
    }

    override fun load(): PersistedSessionState? = state

    override fun clear() {
        state = null
    }
}
