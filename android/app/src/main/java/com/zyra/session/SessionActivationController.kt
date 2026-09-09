package com.zyra.session

class SessionActivationController(
    private val nowSeconds: () -> Long = { System.currentTimeMillis() / 1000L }
) {
    private var _status: SessionStatus = SessionStatus.SignedOut
    val status: SessionStatus get() = _status

    fun begin() {
        _status = SessionStatus.Authenticating
    }

    fun activate(session: ZyraSession) {
        _status = if (session.authenticated && !session.isExpired(nowSeconds())) {
            SessionStatus.Active(session)
        } else {
            SessionStatus.Error("Session rejected or expired")
        }
    }

    fun refresh(session: ZyraSession) {
        activate(session)
    }

    fun signOut() {
        _status = SessionStatus.SignedOut
    }

    fun checkExpiry() {
        val current = _status
        if (current is SessionStatus.Active && current.session.isExpired(nowSeconds())) {
            _status = SessionStatus.Expired(current.session)
        }
    }
}
