const apiClient = (function() {
    let _token = localStorage.getItem('token');

    async function _fetch(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (_token) {
            headers['Authorization'] = `Bearer ${_token}`;
        }

        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const error = new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            error.response = response;
            throw error;
        }
        
        // For 204 No Content
        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    function setToken(token) {
        _token = token;
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    }
    
    return {
        isLoggedIn: () => !!_token,
        
        login: async (email, password) => {
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);
            const data = await _fetch('/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: params
            });
            setToken(data.access_token);
            return data;
        },

        register: (email, password, fullName) => {
            return _fetch('/register', {
                method: 'POST',
                body: JSON.stringify({ email: email, password: password, full_name: fullName })
            });
        },

        logout: () => {
            setToken(null);
        },

        getCurrentUser: (token = null) => {
            if (token) setToken(token);
            return _fetch('/users/me');
        },

        getTrades: () => _fetch('/trades'),

        getHistory: () => _fetch('/history'),

        createTrade: (tradeData) => {
             return _fetch('/trades', {
                method: 'POST',
                body: JSON.stringify(tradeData)
            });
        },

        closeTrade: (tradeId, closePrice) => {
            return _fetch(`/trades/${tradeId}?close_price=${closePrice}`, {
                method: 'DELETE'
            });
        },
        
        closeAllTrades: (prices) => {
            return _fetch('/trades/close-all', {
                method: 'POST',
                body: JSON.stringify({ prices })
            });
        },
        
        checkTriggers: (prices) => {
            return _fetch('/trades/check-triggers', {
                method: 'POST',
                body: JSON.stringify(prices)
            });
        }
    };
})();
