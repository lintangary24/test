// Trading Platform Utilities
class TradingPlatform {
  constructor() {
    this.indicators = new TechnicalIndicators();
    this.riskManager = new RiskManager();
    this.orderManager = new OrderManager();
  }
}

class TechnicalIndicators {
  constructor() {
    this.priceHistory = [];
  }

  addPrice(price) {
    this.priceHistory.push(price);
    if (this.priceHistory.length > 200) {
      this.priceHistory.shift();
    }
  }

  calculateSMA(period) {
    if (this.priceHistory.length < period) return null;
    const sum = this.priceHistory.slice(-period).reduce((a, b) => a + b, 0);
    return sum / period;
  }

  calculateEMA(period) {
    if (this.priceHistory.length < period) return null;
    const multiplier = 2 / (period + 1);
    let ema = this.priceHistory[0];
    
    for (let i = 1; i < this.priceHistory.length; i++) {
      ema = (this.priceHistory[i] * multiplier) + (ema * (1 - multiplier));
    }
    return ema;
  }

  calculateRSI(period = 14) {
    if (this.priceHistory.length < period + 1) return 50;
    
    let gains = 0;
    let losses = 0;
    
    for (let i = this.priceHistory.length - period; i < this.priceHistory.length; i++) {
      const change = this.priceHistory[i] - this.priceHistory[i - 1];
      if (change > 0) gains += change;
      else losses -= change;
    }
    
    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  }

  calculateMACD(fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
    const fastEMA = this.calculateEMA(fastPeriod);
    const slowEMA = this.calculateEMA(slowPeriod);
    
    if (!fastEMA || !slowEMA) return { macd: 0, signal: 0, histogram: 0 };
    
    const macd = fastEMA - slowEMA;
    // Simplified signal line calculation
    const signal = macd * 0.8; // Mock signal line
    const histogram = macd - signal;
    
    return { macd, signal, histogram };
  }

  getBollingerBands(period = 20, stdDev = 2) {
    const sma = this.calculateSMA(period);
    if (!sma || this.priceHistory.length < period) {
      return { upper: 0, middle: 0, lower: 0 };
    }
    
    const recentPrices = this.priceHistory.slice(-period);
    const variance = recentPrices.reduce((sum, price) => {
      return sum + Math.pow(price - sma, 2);
    }, 0) / period;
    
    const standardDeviation = Math.sqrt(variance);
    
    return {
      upper: sma + (standardDeviation * stdDev),
      middle: sma,
      lower: sma - (standardDeviation * stdDev)
    };
  }
}

class RiskManager {
  constructor() {
    this.maxRiskPerTrade = 0.02; // 2% risk per trade
    this.maxDailyLoss = 0.05; // 5% max daily loss
    this.maxOpenPositions = 5;
  }

  calculatePositionSize(accountBalance, stopLossDistance, riskPercent = null) {
    const risk = riskPercent || this.maxRiskPerTrade;
    const riskAmount = accountBalance * risk;
    return riskAmount / stopLossDistance;
  }

  validateTrade(trade, currentPositions, accountInfo) {
    const validation = {
      isValid: true,
      reasons: []
    };

    // Check maximum positions
    if (currentPositions.length >= this.maxOpenPositions) {
      validation.isValid = false;
      validation.reasons.push('Maximum open positions reached');
    }

    // Check margin requirements
    const requiredMargin = trade.volume * 100; // XAUUSD margin requirement
    if (requiredMargin > accountInfo.freeMargin) {
      validation.isValid = false;
      validation.reasons.push('Insufficient margin');
    }

    // Check risk limits
    const riskAmount = Math.abs(trade.stopLoss - trade.price) * trade.volume * 100;
    if (riskAmount > accountInfo.balance * this.maxRiskPerTrade) {
      validation.isValid = false;
      validation.reasons.push('Risk exceeds maximum per trade');
    }

    return validation;
  }
}

class OrderManager {
  constructor() {
    this.orders = [];
    this.orderHistory = [];
  }

  createOrder(orderData) {
    const order = {
      id: Date.now(),
      ...orderData,
      status: 'pending',
      createTime: new Date(),
      updateTime: new Date()
    };

    this.orders.push(order);
    return order;
  }

  executeOrder(orderId, executionPrice) {
    const orderIndex = this.orders.findIndex(order => order.id === orderId);
    if (orderIndex === -1) return null;

    const order = this.orders[orderIndex];
    order.status = 'executed';
    order.executionPrice = executionPrice;
    order.executionTime = new Date();
    order.updateTime = new Date();

    // Move to history
    this.orderHistory.push(order);
    this.orders.splice(orderIndex, 1);

    return order;
  }

  cancelOrder(orderId) {
    const orderIndex = this.orders.findIndex(order => order.id === orderId);
    if (orderIndex === -1) return false;

    const order = this.orders[orderIndex];
    order.status = 'cancelled';
    order.updateTime = new Date();

    // Move to history
    this.orderHistory.push(order);
    this.orders.splice(orderIndex, 1);

    return true;
  }

  getPendingOrders() {
    return this.orders.filter(order => order.status === 'pending');
  }

  getOrderHistory(limit = 50) {
    return this.orderHistory.slice(-limit);
  }
}

// Market Analysis Tools
class MarketAnalyzer {
  constructor() {
    this.supportResistanceLevels = [];
    this.trendDirection = 'sideways';
  }

  analyzeMarketStructure(priceData) {
    // Simplified market structure analysis
    const recentHigh = Math.max(...priceData.slice(-20));
    const recentLow = Math.min(...priceData.slice(-20));
    const currentPrice = priceData[priceData.length - 1];
    
    // Determine trend
    const shortMA = this.calculateMA(priceData, 10);
    const longMA = this.calculateMA(priceData, 20);
    
    if (shortMA > longMA) {
      this.trendDirection = 'uptrend';
    } else if (shortMA < longMA) {
      this.trendDirection = 'downtrend';
    } else {
      this.trendDirection = 'sideways';
    }

    return {
      trend: this.trendDirection,
      support: recentLow,
      resistance: recentHigh,
      currentPrice: currentPrice,
      strength: this.calculateTrendStrength(priceData)
    };
  }

  calculateMA(data, period) {
    if (data.length < period) return 0;
    const sum = data.slice(-period).reduce((a, b) => a + b, 0);
    return sum / period;
  }

  calculateTrendStrength(priceData) {
    // Simplified trend strength calculation
    const adx = Math.random() * 100; // Mock ADX calculation
    if (adx > 50) return 'strong';
    if (adx > 25) return 'moderate';
    return 'weak';
  }

  findSupportResistance(priceData, lookback = 50) {
    const levels = [];
    const data = priceData.slice(-lookback);
    
    // Find local highs and lows
    for (let i = 2; i < data.length - 2; i++) {
      // Local high
      if (data[i] > data[i-1] && data[i] > data[i+1] && 
          data[i] > data[i-2] && data[i] > data[i+2]) {
        levels.push({ price: data[i], type: 'resistance', strength: 1 });
      }
      
      // Local low
      if (data[i] < data[i-1] && data[i] < data[i+1] && 
          data[i] < data[i-2] && data[i] < data[i+2]) {
        levels.push({ price: data[i], type: 'support', strength: 1 });
      }
    }

    return levels;
  }
}

// News and Economic Calendar
class NewsManager {
  constructor() {
    this.newsItems = [];
    this.economicEvents = [];
  }

  addNewsItem(news) {
    this.newsItems.unshift(news);
    if (this.newsItems.length > 100) {
      this.newsItems.pop();
    }
  }

  getRecentNews(limit = 10) {
    return this.newsItems.slice(0, limit);
  }

  addEconomicEvent(event) {
    this.economicEvents.push(event);
    this.economicEvents.sort((a, b) => new Date(a.date) - new Date(b.date));
  }

  getUpcomingEvents(hours = 24) {
    const now = new Date();
    const cutoff = new Date(now.getTime() + hours * 60 * 60 * 1000);
    
    return this.economicEvents.filter(event => {
      const eventDate = new Date(event.date);
      return eventDate >= now && eventDate <= cutoff;
    });
  }
}

// Utility Functions
const Utils = {
  formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(amount);
  },

  formatPrice(price, decimals = 2) {
    return parseFloat(price).toFixed(decimals);
  },

  calculatePips(price1, price2, symbol = 'XAUUSD') {
    // For XAUUSD, 1 pip = 0.01
    return Math.abs(price1 - price2) * 100;
  },

  formatTime(date) {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(date);
  },

  generateOrderId() {
    return 'ORD' + Date.now() + Math.random().toString(36).substr(2, 5).toUpperCase();
  },

  validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
};

// Export for use in main application
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    TradingPlatform,
    TechnicalIndicators,
    RiskManager,
    OrderManager,
    MarketAnalyzer,
    NewsManager,
    Utils
  };
}
