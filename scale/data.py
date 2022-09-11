with open('ns') as file:
    data = file.readlines()

final_data = []
for line in data:
    if "scaleVnfType" in line:
        final_data.append([])
    if "b'scale" in line:
        if len(final_data[-1]) < 2:
            final_data[-1].append(int(line.strip().split(' ')[-1]))
        else:
            final_data.append([final_data[-1][-1] + 61000, int(line.strip().split(' ')[-1])])

scale_out = []
scale_in = []
for i in range(len(final_data)):
    if i%2 == 0:
        scale_out.append(final_data[i])
    else:
        scale_in.append(final_data[i])

for d in (('scale_out.csv', scale_out), ('scale_in.csv', scale_in)):
    with open(d[0], 'w') as file:
        for i in d[1]:
            file.write(str(i[0]) + ',' + str(i[1]) + '\n')
