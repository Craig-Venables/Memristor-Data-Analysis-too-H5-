import h5py

def print_hdf5_structure(file_name):
    with h5py.File(file_name, 'r') as f:
        def print_name(name, obj):
            print(name)
            if isinstance(obj, h5py.Group):
                for key in obj.keys():
                    print_name(f"{name}/{key}", obj[key])

        print_name('/', f)

# Replace 'your_file.h5' with the path to your HDF5 file
print_hdf5_structure('../memristor_data.h5')