import numpy as np
from scipy.stats import norm

def d_values(iv,s,k,r,t):
    """
    iv = implied volatility expressed as a decimal 
    s = stock price
    k = strike price
    r = risk free rate (usually 0.11)
    t = DTE/365
    """
    # values required to execute black-scholes equation
    d1 = 1 / (iv* t**0.5) * ((np.log(s/k)) + (r + iv**2/2) * t)
    d2 = d1 - iv * t**0.5
    return d1, d2

def call_price(iv,s,k,r,t,d1,d2):
    """
    iv = implied volatility expressed as a decimal 
    s = stock price
    k = strike price
    r = risk free rate (usually 0.11)
    t = DTE/365
    d1,d2 = the returned values from "d_values" function
    """
    cprice = norm.cdf(d1) * s - norm.cdf(d2) * k * np.exp(-r * t) # black-scholes
    return cprice

def put_price(iv,s,k,r,t,d1,d2):
    """
    iv = implied volatility expressed as a decimal 
    s = stock price
    k = strike price
    r = risk free rate (usually 0.11)
    t = DTE/365
    d1,d2 = the returned values from "d_values" function
    """
    pprice = -norm.cdf(-d1) * s + norm.cdf(-d2) * k * np.exp(-r*t) # black-scholes
    return pprice

def delta(d1,contract_type):
    """
    d1 = first value returned from "d_values" func
    contract_type = a character ('c' or 'p') indicating whether contract
    is a call or a put
    """
    if contract_type.lower() == 'c':
        return norm.cdf(d1)
    else:
        return -norm.cdf(-d1)

def vega(iv,s,k,r,t):
    """
    iv = implied volatility expressed as a decimal 
    s = stock price
    k = strike price
    r = risk free rate (usually 0.11)
    t = DTE/365
    """
    # vega is the iv's delta
    d1,d2 = d_values(iv,s,k,r,t)
    vega = s * norm.pdf(d1) * t**0.5
    return vega 

def gamma(iv,d2,s,k,r,t):
    """
    iv = implied volatility expressed as a decimal
    d2 = second value returned from "d_values" func
    s = stock price
    k = strike price
    r = risk free rate (usually 0.11)
    t = DTE/365
    """
    # gamma is essentially the delta's delta
    return (k*np.exp(-r*t) * (norm.pdf(d2) / (s**2 * iv * (t**0.5))))

def theta(iv,d1,d2,s,k,r,t,contract_type):
    """
    iv = implied volatility expressed as a decimal
    d1,d2 = returned values from "d_values" func
    s = stock price
    k = strike price
    r = risk free rate (usually 0.11)
    t = DTE/365
    contract_type = a character ('c' or 'p') indicating whether contract is
    a call or a put
    """
    # theta is the time decay, for each day contract will drop in n value
    if contract_type.lower() == 'p':
        theta = -s * iv * norm.pdf(-d1) / (2*t**0.5) + r * k * np.exp(-r*t)*norm.cdf(d2)
    else:
        theta = -s * iv * norm.pdf(d1) / (2*t**0.5) - r * k * np.exp(-r*t)*norm.cdf(d2)
    return theta