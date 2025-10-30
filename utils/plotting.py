import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score

def polyfit1d_and_plot(df, var1, var2, xlabel, title):
    """ Make plots and polyfit lines for regression analysis
    
    Args:
        df (pd.Dataframe): Dataframe values
        var1, var2 (str): variables to plot
        xlabel (str): X-axis label
        title (str): Title of plot
        
    Returns: 
        fig
    """
    coef = np.polyfit(df[var1], df[var2], 1)
    poly1d_fn = np.poly1d(coef)
    r2 = r2_score(df[var1], poly1d_fn(df[var2]))
    
    fig, ax = plt.subplots(1,1)
    ax.scatter(df[var1], df[var2])
    ax.plot(df[var1],poly1d_fn(df[var1]), color="red", label=f"$R^2$: {r2:.2f}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("RMSE (FluxNet vs MiCASA)")
    ax.set_title(title)
    ax.legend(loc="upper left")
    return fig

