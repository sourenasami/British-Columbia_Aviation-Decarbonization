import calliope
model = calliope.Model('model.yaml')
model.run()
model.to_csv('csv_results/2050')
#model.plot.capacity()
#model.plot.timeseries()

