import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Force TrueType embedding in PDF/PS
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

# Font settings
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans']
# Load data
df = pd.read_csv("filepath_to_micromobility_csv")

# Extract lon, lat from "POINT (lon lat)"
df[['lon', 'lat']] = df['geometry'].str.extract(r'POINT \(([^ ]+) ([^ ]+)\)').astype(float)

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp_requested'])

# Use fine precision (almost raw)
df['lat_raw'] = df['lat'].round(5)   # ~1m precision
df['lon_raw'] = df['lon'].round(5)

df['time_raw'] = df['timestamp']     # exact time
df['crm_raw'] = df['current_range_meters']

# Define group
groups_before = df.groupby(['lat_raw', 'lon_raw', 'time_raw', 'crm_raw'])

# Group sizes
group_sizes_before = groups_before.size().values

df['lat_coarse'] = df['lat'].round(3)
df['lon_coarse'] = df['lon'].round(3)

def time_bin(hour):
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    else:
        return "night"

df['time_coarse'] = df['timestamp'].dt.hour.apply(time_bin)

df['crm_coarse'] = np.floor(df['current_range_meters'] / 1000)  # you can adjust bin size

groups_after = df.groupby(['lat_coarse', 'lon_coarse', 'time_coarse', 'crm_coarse'])

group_sizes_after = groups_after.size().values

plt.figure()

plt.hist(group_sizes_before, bins=20, alpha=0.5, label="Before Coarsening")
plt.hist(group_sizes_after, bins=20, alpha=0.5, label="After Coarsening")

plt.xlabel("Group Size")
plt.ylabel("Frequency")
plt.legend()

plt.title("Group Size Distribution Before and After Coarsening")

plt.show()


def plot_cdf(data, label):
    sorted_data = np.sort(data)
    yvals = np.arange(len(sorted_data)) / float(len(sorted_data))
    plt.plot(sorted_data, yvals, label=label)
    
def weighted_cdf(group_sizes):
    sorted_sizes = np.sort(group_sizes)
    weights = sorted_sizes  # each group weighted by its size

    cum_weights = np.cumsum(weights)
    cum_weights = cum_weights / cum_weights[-1]

    return sorted_sizes, cum_weights

x_before, y_before = weighted_cdf(group_sizes_before)
x_after, y_after = weighted_cdf(group_sizes_after)


plt.plot(x_before, y_before, label="Before Coarsening")
plt.plot(x_after, y_after, label="After Coarsening")

plt.figure()

plot_cdf(group_sizes_before, "Before Coarsening")
plot_cdf(group_sizes_after, "After Coarsening")

plt.xlabel("Group Size", fontsize=12, fontweight='bold')
plt.ylabel("Cumulative Distribution", fontsize=12, fontweight='bold')
plt.xticks(fontweight='bold', fontsize=12)
plt.yticks(fontweight='bold', fontsize=12)

# plt.xlim(1,50)
# plt.xscale('log')
plt.legend(prop={'weight':'bold', 'size':12})

# plt.title("CDF of Group Sizes")



# plt.savefig("C:\\Users\\Debasree Das\\Desktop\\Explanym\\paper_work\\popets_2026\\coarsening.pdf", format='pdf', bbox_inches='tight')
plt.savefig("coarsening.eps", format='eps', bbox_inches='tight')

plt.show()

singleton_before = np.mean(group_sizes_before == 1)
singleton_after = np.mean(group_sizes_after == 1)

print("Singleton Before:", singleton_before)
print("Singleton After:", singleton_after)
