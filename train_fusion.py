import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init
import torch
from torch import optim
import matplotlib.pyplot as plt
import numpy as np
training_losses = []
val_losses = []
val_accuracies = []
training_accuracies = []
best_model = None
best_epoch = 0


def evaluate_model(model, criterion, data_loader):
    loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in data_loader:
            outputs = model(inputs)
            if model.intermediate_layers: # in case of multiple layers, average the loss over each layer
                for output in outputs:
                    loss += criterion(output, labels).item() * inputs.size(0)/len(outputs)
                # only the final output is used for prediction accuracy
                _, predicted = torch.max(outputs[0], 1)
            else:
                loss += criterion(outputs, labels).item() * inputs.size(0)
                _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # Calculate average loss and accuracy
    avg_loss = loss / len(data_loader.dataset)
    accuracy = correct / total

    return avg_loss, accuracy

def train(model: nn.Module, 
          train_loader, 
          val_loader, 
          criterion, 
          optimizer: torch.optim.Adam, 
          epochs: int,
          decrease_learning_rate = False):            #change last option to 'true' to implement decreasing learning rate for choice task 1
    print("Starting training...")
    best_val_accuracy = 1e10
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}")
        print("=====================================")
        # if deacrease_learning_rate is set to True:
        if decrease_learning_rate and epoch > 0 and epoch % 4 == 0:
            # halves learning rate every 5th epoch for choice task #1
            for param_group in optimizer.param_groups:
                lr = param_group['lr']
                lr /= 2
                param_group['lr'] = lr 
            print(f"Halved learning rate to {lr}")

        train_loss = 0.0
        interval = int(len(train_loader)/8)
        for i, (inputs, labels) in enumerate(train_loader):
            optimizer.zero_grad()

            # if the model implements intermediate layers, this will average the loss of each layer
            # if the model has only one layer, it works as normal
            outputs = model(inputs)
            if model.intermediate_layers:
                loss = 0
                for output in outputs:
                    loss += criterion(output, labels)/len(outputs)
            else:
                loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * inputs.size(0)

            if i % interval == 0 or i == len(train_loader):  # Print when a batch is completed or it's the last batch
                avg_train_loss = train_loss / ((i + 1) * 1) 
                print(f"Batch: {i:>3}/{len(train_loader)}, training loss: {avg_train_loss:.4f}")

        val_loss, val_accuracy = evaluate_model(model, criterion, val_loader)
        if val_accuracy < best_val_accuracy:
            best_val_accuracy = val_accuracy
            best_epoch = epoch + 1
            best_model = model.state_dict()
            print("This is the best model so far. Hurray.")

        T_loss, T_acc = evaluate_model(model, criterion, train_loader)

        val_losses.append(val_loss)
        val_accuracies.append(val_accuracy)
        training_accuracies.append(T_acc)
        training_losses.append(T_loss)
        print("—————————————————————————————————————")
        print(f'Validation Loss: {val_loss:>20.4f}\nValidation Accuracy: {val_accuracy:>16.4f}')
        print(f'Training Loss: {T_loss:>22.4f}\nTraining Accuracy: {T_acc:>18.4f}\n')
    
    print(f"Finished training after {epochs} epochs")
    print(f"Best epoch: {best_epoch}")

import matplotlib.pyplot as plt
import numpy as np

def plot_graphs(training_loss, eval_loss, training_accuracy, eval_accuracy, title):
    _, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

    # Plot training and eval loss over time
    epochs = np.arange(1, len(training_loss) + 1)
    axes[0].plot(epochs, training_loss, label='Training Loss', color='black')
    axes[0].plot(epochs, eval_loss, label='Eval Loss', color='gray', linestyle='--')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_xticks(epochs)
    axes[0].legend()
    axes[0].set_title('Training and Eval Loss')

    # Plot training and eval accuracy over time
    axes[1].plot(epochs, training_accuracy, label='Training Accuracy', color='black')
    axes[1].plot(epochs, eval_accuracy, label='Eval Accuracy', color='gray', linestyle='--')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_xticks(epochs)
    axes[1].legend()
    axes[1].set_title('Training and Eval Accuracy')

    # Set overarching title
    plt.suptitle(title, fontsize=16)

    plt.tight_layout()
    plt.savefig(f"results/{title}.png")

def savemodel(model_name):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{model_name}_epoch_{best_epoch}_{timestamp}"
    plot_graphs(training_losses,val_losses, training_accuracies, val_accuracies , filename)

    print(f"Saving best model to {filename}.pth")
    torch.save(best_model, f"trained_models/{storage_location}/{filename}.pth")

if __name__ == "__main__":
    import signal
    import sys
    from datetime import datetime
    from sys import argv

    # train_model "model path" "dataset" 
    model_path = argv[1]
    dataset = argv[2]
    epochs = int(argv[3])
    if len(argv) >4:
        weights_path = argv[4]
    else:
        weights_path = None
    import importlib.util

    def load_python_file(file_path):
        spec = importlib.util.spec_from_file_location("model", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    model: torch.nn.Module = load_python_file(model_path).model()

    # Load weights if provided
    if weights_path:
        model.load_state_dict(torch.load(weights_path))


    if dataset == "OF":
        from data.HMDB51.dataset import optical_flow_test_dataloader, optical_flow_train_dataloader
        test_data = optical_flow_test_dataloader
        training_data = optical_flow_train_dataloader
        storage_location = "optical_flow"
    if dataset == "HMDB_frames":
        from data.HMDB51.dataset import mid_frame_test_dataloader, mid_frame_train_dataloader
        test_data = mid_frame_test_dataloader
        training_data = mid_frame_train_dataloader
        storage_location = "frames/HMDB"

    if dataset == "stanford_frames":
        from data.stanford40.dataset import val_dataloader, test_dataloader, train_dataloader
        storage_location = "frames/stanford"
        val_data = val_dataloader
        training_data = train_dataloader
        test_data = test_dataloader

    print(f"training {model.name} from {model_path} on {storage_location} data.")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr= 0.001)
    def signal_handler(sig, frame):
        # This function will be called when a keyboard interrupt is detected
        print('Keyboard interrupt detected. Storing best model...')
        savemodel(f"{model.name}_interupted")
        sys.exit(0)
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # grid search

    train(  model, 
            training_data, 
            val_data, 
            criterion, 
            optimizer, 
            epochs,
            decrease_learning_rate=False)
    savemodel(f"{model.name}")


###### CHATGPT

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision.datasets import YourDataset  # Import your dataset class
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from torchvision.models import YourPretrainedModel  # Import your pretrained model class
from sklearn.model_selection import train_test_split

# Define your FusionModel class here (same as before)

# Define hyperparameters
batch_size = 32
learning_rate = 0.001
num_epochs = 10
num_classes = 10  # Adjust this according to your dataset

# Define your dataset and data loaders
transform = transforms.Compose([
    # Add your desired transformations here
    transforms.Resize((224, 224)),  # Example transformation, adjust as needed
    transforms.ToTensor(),
])

# Example: Splitting dataset into train and test sets
# Replace with your own dataset loading and splitting logic
dataset = YourDataset(transform=transform)
train_set, test_set = train_test_split(dataset, test_size=0.2, random_state=42)

train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

# Initialize pre-trained models for optical flow and regular images
cnn_opticalflow = YourPretrainedModel()  # Replace with your own pre-trained model
cnn_image = YourPretrainedModel()  # Replace with your own pre-trained model

# Initialize the fusion model
fusion_model = FusionModel(cnn_opticalflow, cnn_image, fusion_dim=512, num_classes=num_classes)

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(fusion_model.parameters(), lr=learning_rate)

# Training loop
for epoch in range(num_epochs):
    fusion_model.train()
    running_loss = 0.0
    
    for batch_idx, (opticalflow, image, labels) in enumerate(train_loader):
        optimizer.zero_grad()
        
        # Forward pass
        outputs = fusion_model(opticalflow, image)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        
        if batch_idx % 100 == 99:
            print(f'Epoch {epoch+1}, Batch {batch_idx+1}/{len(train_loader)}, Loss: {running_loss/100:.4f}')
            running_loss = 0.0

# Evaluation loop
fusion_model.eval()
correct = 0
total = 0

with torch.no_grad():
    for opticalflow, image, labels in test_loader:
        outputs = fusion_model(opticalflow, image)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print(f'Accuracy on test set: {100 * correct / total:.2f}%')
